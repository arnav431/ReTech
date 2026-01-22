from flask import Flask, render_template, request, jsonify, redirect, url_for, session, send_from_directory
import importlib.util
import firebase_admin 
from firebase_admin import credentials, firestore, initialize_app, auth
from dotenv import load_dotenv
from functools import wraps
import os
from google import genai
import json
import re
import requests

load_dotenv()

app = Flask(
    __name__,
    template_folder='src/templates',
    static_folder='src'
)
    

# Use a stable secret key so session cookies stay valid between requests / reloads
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-me')
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = True  # keep False for local HTTP; set True in production with HTTPS


CUSTOM_SEARCH_KEY = os.getenv("CUSTOM_SEARCH_KEY")  # For Custom Search ONLY
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")        # For Gemini ONLY
CHAT_GEMINI_API_KEY = os.getenv("CHAT_GEMINI_API_KEY", GEMINI_API_KEY)
CSE_ID = os.getenv("CSE_ID")

# ---------- GEN AI Specs Helper ----------

def clean_json_text(text: str) -> str:
    text = re.sub(r"^```(?:json)?", "", text.strip(), flags=re.MULTILINE)
    text = re.sub(r"```$", "", text.strip(), flags=re.MULTILINE)
    return text.strip()


def search_specs(query: str) -> dict:
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "q": query,
        "key": CUSTOM_SEARCH_KEY,
        "cx": CSE_ID
    }
    return requests.get(url, params=params).json()


# ---------- generating AI specs ----------

def get_specs_from_gemini(query: str) -> dict:
    """Generate compact product specs using Gemini"""

    search_results = search_specs(query)

    snippets = "\n".join(
        item.get("snippet", "")
        for item in search_results.get("items", [])
    )

    # Create Gemini client
    client = genai.Client(api_key=GEMINI_API_KEY)

    prompt = f"""
You are a strict JSON generation system.

The output will be parsed directly using json.loads().
If the output is not valid JSON, it will cause a system failure.

Context (from web search):
{snippets}

Task:
Extract compact product card data for "{query}".

Rules (MANDATORY):
- Output ONLY raw JSON
- Do NOT include markdown, comments, explanations, or backticks
- Include ALL fields exactly as defined
- Use empty strings "" if data is unknown
- Use numbers only for numeric fields
- Keep total JSON under 1KB
- Use market-level, summarized information only
- Approximate prices if exact price is unavailable
- If unsure, still return valid JSON with empty values

Data expectations:
- Provide camera megapixel details (e.g., "48MP + 12MP")
- Provide battery capacity in mAh when possible
- Provide RAM in GB and storage in GB
- Provide chipset model (e.g., "Apple A18")
- Provide Antutu score if available (string value)

Required JSON schema (must match exactly):
{{
  "id": "",
  "name": "",
  "brand": "",
  "category": "",
  "description": "",
  "price": 0,
  "original_price": 0,
  "discount_percentage": 0,
  "image": "",
  "condition": "New",
  "stock": 0,
  "rating": 0,
  "reviews": 0,
  "specs": {{
    "display": "",
    "chipset": "",
    "ram": "",
    "storage": "",
    "battery": "",
        "camera": "",
        "antutu": ""
  }},
  "tags": []
}}

Output:
"""

    # Generate content using Gemini
    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=prompt
    )

    text = clean_json_text(response.text)

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Safe fallback
        return {
            "id": "",
            "name": query,
            "brand": "",
            "category": "",
            "description": text,
            "price": 0,
            "original_price": 0,
            "discount_percentage": 0,
            "image": "",
            "condition": "New",
            "stock": 0,
            "rating": 0,
            "reviews": 0,
            "specs": {
                "display": "",
                "chipset": "",
                "ram": "",
                "storage": "",
                "battery": "",
                "camera": "",
                "antutu": ""
            },
            "tags": []
        }


firebase_available = False
db = None

try:
    firebase_json = os.getenv("FIREBASE_CREDENTIALS_JSON")

    if not firebase_json:
        raise ValueError("FIREBASE_CREDENTIALS_JSON not set")

    # Parse JSON from ENV
    cred_dict = json.loads(firebase_json)

    cred = credentials.Certificate(cred_dict)

    # Prevent double initialization
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)

    db = firestore.client()
    firebase_available = True

    print("✅ Firebase initialized successfully")

except Exception as e:
    firebase_available = False
    db = None
    print("❌ Firebase initialization failed")
    print("Reason:", e)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        identifier = request.form.get("username")  # email OR username
        password = request.form.get("password")

        # ---- Root login ----
        if identifier == "root" and password == "root":
            session["logged_in"] = True
            session["sessionUsername"] = "root"
            session["sessionEmail"] = "root@localhost"
            return redirect(url_for("shop"))


        if not firebase_available:
            return render_template(
                "auth/login.html",
                error="Database not available"
            )

        # ---- Find user by email or username ----
        user_query = (
            db.collection("users")
            .where("email", "==", identifier)
            .limit(1)
            .get()
        )

        if not user_query:
            user_query = (
                db.collection("users")
                .where("username", "==", identifier)
                .limit(1)
                .get()
            )

        if not user_query:
            return render_template(
                "auth/login.html",
                error="Invalid username or password"
            )

        user = user_query[0].to_dict()

        # ---- Password check ----
        if user["password"] != password:
            return render_template(
                "auth/login.html",
                error="Invalid username or password"
            )

        # ---- Login success ----
        session["logged_in"] = True
        session["sessionUsername"] = user["username"]
        session["sessionEmail"] = user["email"]

        return redirect(url_for("shop"))

    return render_template("auth/login.html")

@app.route("/auth/google", methods=["POST"])
def google_auth():
    id_token = request.json.get("idToken")

    try:
        decoded = auth.verify_id_token(id_token)

        uid = decoded["uid"]
        email = decoded.get("email")
        name = decoded.get("name") or email.split("@")[0]

        # 🔍 Check if user exists
        user_query = (
            db.collection("users")
            .where("email", "==", email)
            .limit(1)
            .get()
        )

        # 🆕 If user does NOT exist → REGISTER
        if not user_query:
            db.collection("users").add({
                "uid": uid,
                "username": name,
                "email": email,
                "auth_provider": "google"
            })

        # ✅ Login (for both cases)
        session["logged_in"] = True
        session["sessionUsername"] = name
        session["sessionEmail"] = email
        session["user_id"] = uid

        return jsonify({"success": True})

    except Exception as e:
        print("Google auth error:", e)
        return jsonify({"error": "Invalid token"}), 401


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")
        terms = request.form.get("terms")
        print([username,email,password])

        # ---- Validation ----
        if not all([username, email, password, confirm_password, terms]):
            print("something was left\n")
            return render_template(
                "auth/signup.html",
                error="All fields are required"
            )

        if password != confirm_password:
            print("Passwords do not match\n")
            return render_template(
                "auth/signup.html",
                error="Passwords do not match"
            )

        if not firebase_available:
            print("Database not available. Try again later.")
            return render_template(
                "auth/signup.html",
                error="Database not available. Try again later."
                

            )

        # ---- Check if email already exists ----
        existing_user = db.collection("users").where("email", "==", email).limit(1).get()
        if existing_user:
            print("email already exists")
            return render_template(
                "auth/signup.html",
                error="Email already registered"
            )

        # ---- from werkzeug.security import generate_password_hash can be used to create hashed passwords ----
        #hashed_password = generate_password_hash(password)

        db.collection("users").add({
            "username": username,
            "email": email,
            "password": password
        })
        print([username,email,password])
        return redirect(url_for("login"))

    return render_template("auth/signup.html")

@app.route("/logout")
def logout():
    session.clear()
    session.modified = True
    return render_template("auth/login.html")

@app.route("/shop")
@login_required
def shop():
    products = []
    print(dict(session))
    if firebase_available:
        try:
            products_ref = db.collection('products')
            products = [doc.to_dict() for doc in products_ref.stream()]
        except Exception as e:
            print(f"Error fetching products: {e}")
    return render_template("/shop.html", products=products)

@app.route("/sell")
@login_required
def sell():
    return render_template("sell.html")

@app.route("/admin/products")
@login_required
def admin_products():
    """Admin interface for managing products"""
    return render_template("admin/products.html")

@app.route("/api/products", methods=["GET"])
@login_required
def get_products():
    if not firebase_available:
        return jsonify({"status": "error", "message": "Database not available"}), 503
    
    try:
        products_ref = db.collection('products')
        products = [doc.to_dict() for doc in products_ref.stream()]
        return jsonify({"status": "success", "products": products})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/shop/products", methods=["GET"])
@login_required
def get_shop_products():
    """Get products for the shop page with categories"""
    try:
        # Load products from JSON file
        import json
        import os
        
        products_file = os.path.join(app.root_path, 'src', 'data', 'products.json')
        
        if os.path.exists(products_file):
            with open(products_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return jsonify({
                    "status": "success", 
                    "products": data.get('products', []),
                    "categories": data.get('categories', [])
                })
        else:
            # Fallback to Firebase if JSON file doesn't exist
            if firebase_available:
                products_ref = db.collection('products')
                products = [doc.to_dict() for doc in products_ref.stream()]
                return jsonify({
                    "status": "success", 
                    "products": products,
                    "categories": []
                })
            else:
                return jsonify({
                    "status": "error", 
                    "message": "No product data available"
                }), 404
                
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/products", methods=["POST"])
@login_required
def add_product():
    if not firebase_available:
        return jsonify({"status": "error", "message": "Database not available"}), 503
    
    try:
        data = request.json
        required_fields = ["name", "description", "price", "condition", "category"]
        
        if not all(field in data for field in required_fields):
            return jsonify({"status": "error", "message": "Missing required fields"}), 400

        doc_ref = db.collection('products').document()
        doc_ref.set({
            "id": doc_ref.id,
            "name": data["name"],
            "description": data["description"],
            "price": float(data["price"]),
            "condition": data["condition"],
            "category": data["category"],
            "images": data.get("images", []),
            "created_at": firestore.SERVER_TIMESTAMP
        })

        return jsonify({"status": "success", "product_id": doc_ref.id})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/products/<product_id>", methods=["GET"])
@login_required
def get_product(product_id):
    if not firebase_available:
        return jsonify({"status": "error", "message": "Database not available"}), 503
    
    try:
        doc_ref = db.collection('products').document(product_id)
        product = doc_ref.get()
        
        if product.exists:
            return jsonify({"status": "success", "product": product.to_dict()})
        return jsonify({"status": "error", "message": "Product not found"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/admin/products", methods=["POST"])
@login_required
def admin_add_product():
    """Add a new product to the JSON file"""
    try:
        import json
        import os
        import uuid
        
        data = request.json
        required_fields = ["name", "brand", "category", "description", "price", "image", "stock"]
        
        if not all(field in data for field in required_fields):
            return jsonify({"status": "error", "message": "Missing required fields"}), 400

        # Load existing products
        products_file = os.path.join(app.root_path, 'src', 'data', 'products.json')
        
        if os.path.exists(products_file):
            with open(products_file, 'r', encoding='utf-8') as f:
                file_data = json.load(f)
        else:
            file_data = {"products": [], "categories": []}

        # Create new product
        new_product = {
            "id": str(uuid.uuid4()),
            "name": data["name"],
            "brand": data["brand"],
            "category": data["category"],
            "description": data["description"],
            "price": float(data["price"]),
            "original_price": float(data.get("original_price", data["price"])),
            "discount_percentage": float(data.get("discount_percentage", 0)),
            "image": data["image"],
            "condition": data.get("condition", "New"),
            "stock": int(data["stock"]),
            "rating": float(data.get("rating", 0)),
            "reviews": int(data.get("reviews", 0)),
            "specs": data.get("specs", {}),
            "tags": data.get("tags", [])
        }

        # Add to products list
        file_data["products"].append(new_product)

        # Save back to file
        with open(products_file, 'w', encoding='utf-8') as f:
            json.dump(file_data, f, indent=2, ensure_ascii=False)

        return jsonify({"status": "success", "product_id": new_product["id"]})
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

def _sanitize_chat_history(raw_history):
    if not isinstance(raw_history, list):
        return []
    cleaned = []
    for item in raw_history:
        if not isinstance(item, dict):
            continue
        role = (item.get("role") or "user").strip().lower()
        if role not in {"user", "assistant"}:
            role = "user"
        content = (item.get("content") or "").strip()
        if content:
            cleaned.append({"role": role, "content": content})
    return cleaned


@app.route("/api/chat/history", methods=["GET"])
@login_required
def get_chat_history():
    history = session.get("chat_history", [])
    return jsonify({"status": "success", "history": history})


@app.route("/api/chat/history", methods=["DELETE"])
@login_required
def clear_chat_history():
    session.pop("chat_history", None)
    session.modified = True
    return jsonify({"status": "success"})


@app.route("/api/chat", methods=["POST"])
@login_required
def chat():
    data = request.json or {}
    message = (data.get("message") or "").strip()
    client_history = data.get("history", [])

    if not message:
        return jsonify({"status": "error", "message": "Message is required"}), 400

    if not CHAT_GEMINI_API_KEY:
        return jsonify({"status": "error", "message": "Chat API key not configured"}), 500

    try:
        client = genai.Client(api_key=CHAT_GEMINI_API_KEY)

        history = session.get("chat_history", [])
        if not history and client_history:
            history = _sanitize_chat_history(client_history)

        history = _sanitize_chat_history(history)

        # Add the user's latest message to history (avoid duplicating if client already sent it)
        if not (history and history[-1].get("role") == "user" and history[-1].get("content") == message):
            history.append({"role": "user", "content": message})

        history_lines = []
        for item in history[-7:-1]:
            role = (item.get("role") or "user").capitalize()
            content = (item.get("content") or "").strip()
            if content:
                history_lines.append(f"{role}: {content}")

        history_text = "\n".join(history_lines)

        prompt = f"""
You are "Ghost", an AI assistant for a second-hand electronics marketplace.
Your role is to help users BUY and SELL used electronics safely and confidently.

Also give short answers.

When ever it is asked lik who made you/ developed you then you have to say i was developed by the HackWolves.
Also take care of any such question don't say you're gemini or were made by Google.
Personality & Tone:
- Friendly, smart, and trustworthy
- Casual but professional (not slang-heavy)
- Clear, honest, and transparent
- Never pushy or manipulative

Core Responsibilities:
1. Help users find used electronics (phones, laptops, accessories, gadgets, etc.)
2. Help users sell their electronics by guiding them on:
   - Device condition
   - Fair resale price
   - Required details (brand, model, storage, age, issues)
3. Answer questions about:
   - Pricing
   - Device condition grades (like: Excellent, Good, Fair)
   - Buy/sell process
   - Safety tips for second-hand purchases
4. Assist with comparisons between devices when requested
5. Explain store policies clearly if asked

Buying Rules:
- Recommend devices based on user needs and budget
- Always mention condition, warranty (if any), and return policy
- Never guarantee “brand-new” quality for used devices
- Be honest about trade-offs

Selling Rules:
- Ask clear follow-up questions if info is missing
- Suggest a realistic price range (not inflated)
- Warn users to remove personal data before selling
- Mention basic checks (battery health, screen damage, accessories)

Safety & Trust:
- Never request OTPs, passwords, or sensitive personal data
- Encourage secure payment and verified listings
- If unsure about information, say so instead of guessing

Data Handling:
- If product data is provided, use ONLY that data
- Do NOT invent prices, stock, or policies
- If data is missing, ask the user politely

Fallback Behavior:
- If a question is outside your scope, explain briefly and redirect
- If the user is confused, guide step-by-step

End Goal:
Help users make confident decisions while buying or selling second-hand electronics, with honesty and clarity.


Conversation:
{history_text}
User: {message}
Assistant:
"""

        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=prompt
        )

        reply = (response.text or "").strip()
        if not reply:
            reply = "Sorry, I couldn’t generate a response right now."

        history.append({"role": "assistant", "content": reply})
        session["chat_history"] = history[-20:]
        session.modified = True

        return jsonify({"status": "success", "reply": reply, "history": session["chat_history"]})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/admin/products/<product_id>", methods=["DELETE"])
@login_required
def admin_delete_product(product_id):
    """Delete a product from the JSON file"""
    try:
        import json
        import os
        
        products_file = os.path.join(app.root_path, 'src', 'data', 'products.json')
        
        if not os.path.exists(products_file):
            return jsonify({"status": "error", "message": "Products file not found"}), 404

        with open(products_file, 'r', encoding='utf-8') as f:
            file_data = json.load(f)

        # Find and remove product
        products = file_data["products"]
        product_index = None
        
        for i, product in enumerate(products):
            if product["id"] == product_id:
                product_index = i
                break

        if product_index is None:
            return jsonify({"status": "error", "message": "Product not found"}), 404

        # Remove product
        del products[product_index]

        # Save back to file
        with open(products_file, 'w', encoding='utf-8') as f:
            json.dump(file_data, f, indent=2, ensure_ascii=False)

        return jsonify({"status": "success", "message": "Product deleted"})
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/<path:path>")
def catch_all(path):
    # Serve static files if they exist
    if path.startswith("src/images/"):
        filename = path.replace("src/images/", "")
        return send_from_directory("src/images", filename)
    elif path.startswith("src/static/"):
        filename = path.replace("src/static/", "")
        return send_from_directory("src/static", filename)
    elif path.startswith("src/scripts/"):
        filename = path.replace("src/scripts/", "")
        return send_from_directory("src/scripts", filename)
    if path.startswith("src/videos/"):
        filename = path.replace("src/videos/", "")
        return send_from_directory("src/videos", filename)
    if path.startswith("src/annimations/"):
        filename = path.replace("src/annimations/", "")
        return send_from_directory("src/annimations", filename)
    else:
        return render_template("index.html")


# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

# --- AI Device Spec Generation Endpoint ---
@app.route('/api/generate-specs', methods=['POST'])
@login_required
def generate_specs():
    data = request.json or {}
    # Compose device query from available fields
    query_parts = [
        data.get('brand', ''),
        data.get('model', ''),
        data.get('category', ''),
        data.get('storage', ''),
        data.get('color', ''),
    ]
    query = " ".join([part for part in query_parts if part]).strip()
    if not query:
        return jsonify({'status': 'error', 'message': 'Insufficient device info'}), 400
    
    try:
        specs = get_specs_from_gemini(query)
        if not isinstance(specs, dict):
            return jsonify({'status': 'error', 'message': 'Invalid AI response'}), 500

        # Prefer AI description, fallback to bullet list from specs
        description = specs.get('description', '')
        specs_block = specs.get('specs', {}) if isinstance(specs.get('specs', {}), dict) else {}
        bullet_desc = []
        if specs_block:
            for k, v in specs_block.items():
                if v:
                    bullet_desc.append(f"• {k.capitalize()}: {v}")
        if not description and bullet_desc:
            description = '\n'.join(bullet_desc)
        elif description and bullet_desc:
            description = f"{description}\n\n" + "\n".join(bullet_desc)

        # Merge request data (user-provided fields take priority if AI returned empty)
        merged_specs = {
            **specs,
            'brand': specs.get('brand') or data.get('brand', ''),
            'name': specs.get('name') or data.get('model', data.get('name', '')),
            'category': specs.get('category') or data.get('category', ''),
            'description': description,
            'specs': specs_block,
        }

        # Save to session for later submission
        price = data.get('expected_price')
        session['pending_product'] = {**data, 'description': description, 'specs': merged_specs, 'price': price}
        return jsonify({'status': 'success', 'description': description, 'specs': merged_specs})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/submit-listing', methods=['POST'])
@login_required
def submit_listing():
    import json, os, uuid
    pending = session.pop('pending_product', None)
    if not pending:
        return jsonify({'status': 'error', 'message': 'No pending product to submit.'}), 400
    # Prepare product object (ensure required fields)
    product = {
        "id": str(uuid.uuid4()),
        "name": pending.get('model', pending.get('name', '')),
        "brand": pending.get('brand', ''),
        "category": pending.get('category', ''),
        "description": pending.get('description', ''),
        "price": float(pending.get('expected_price', pending.get('price', 0))),
        "original_price": float(pending.get('original_price', 0)),
        "discount_percentage": float(pending.get('discount_percentage', 0)),
        "image": pending.get('image', ''),
        "condition": pending.get('condition', 'New'),
        "stock": int(pending.get('stock', 1)),
        "rating": float(pending.get('rating', 0)),
        "reviews": int(pending.get('reviews', 0)),
        "specs": pending.get('specs', {}),
        "tags": pending.get('tags', [])
    }
    # Save to products.json
    products_file = os.path.join(app.root_path, 'src', 'data', 'products.json')
    if os.path.exists(products_file):
        with open(products_file, 'r', encoding='utf-8') as f:
            file_data = json.load(f)
    else:
        file_data = {"products": [], "categories": []}
    file_data["products"].append(product)
    with open(products_file, 'w', encoding='utf-8') as f:
        json.dump(file_data, f, indent=2, ensure_ascii=False)
    return jsonify({'status': 'success', 'product_id': product['id']})

@app.route('/product/<product_id>')
def product_page(product_id):
    import json, os
    products_file = os.path.join(app.root_path, 'src', 'data', 'products.json')
    if os.path.exists(products_file):
        with open(products_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            product = next((p for p in data.get('products', []) if p['id'] == product_id), None)
            if product:
                return render_template('product.html', product=product)
    return render_template('404.html'), 404

if __name__ == "__main__":
    app.run(debug=True)
