from flask import Flask, render_template, request, jsonify, redirect, url_for, session, send_from_directory
from firebase_admin import credentials, firestore, initialize_app
from dotenv import load_dotenv
from functools import wraps
import os

# Load environment variables
load_dotenv()

app = Flask(__name__, 
            template_folder='src/templates',  # Set the template folder explicitly
            static_folder='src/static')       # Set the static folder explicitly
app.secret_key = os.urandom(24)  # For session management

# Catch-all route that returns um.html for any path
@app.route("/", defaults={"path": ""})
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
    else:
        return render_template("um.html")



'''
# Initialize Firebase with fallback
firebase_available = False
db = None

try:
    if os.getenv('FIREBASE_CREDENTIALS_PATH'):
        cred = credentials.Certificate(os.getenv('FIREBASE_CREDENTIALS_PATH'))
        firebase_app = initialize_app(cred)
        db = firestore.client()
        firebase_available = True
    else:
        print("Firebase credentials not found, running in fallback mode")
except Exception as e:
    print(f"Firebase initialization failed: {e}")
    print("Running in fallback mode with root user only")

# Login decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route("/")
def home():
    return render_template("um.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username == "root" and password == "root":
            session["logged_in"] = True
            session["username"] = username
            return redirect(url_for("shop"))
        else:
            return render_template("auth/login.html", error="Invalid username or password")
    
    return render_template("/auth/login.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")
        terms = request.form.get("terms")

        # Basic validation
        if not all([username, email, password, confirm_password, terms]):
            return render_template("auth/signup.html", error="All fields are required")
        
        if password != confirm_password:
            return render_template("auth/signup.html", error="Passwords do not match")

        # TODO: Add Firebase user creation
        # For now, just redirect to login
        return redirect(url_for("login"))
    
    return render_template("/auth/signup.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

@app.route("/shop")
@login_required
def shop():
    products = []
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


'''

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

if __name__ == "__main__":
    app.run(debug=True)
