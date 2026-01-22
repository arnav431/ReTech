import requests
import json
import re
import os
from dotenv import load_dotenv
from google import genai

# Load environment variables
load_dotenv()

CUSTOM_SEARCH_KEY = os.getenv("CUSTOM_SEARCH_KEY")  # For Custom Search ONLY
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")        # For Gemini ONLY
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
    "camera": ""
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
                "camera": ""
            },
            "tags": []
        }


# ---------- Test ----------

if __name__ == "__main__":
    specs = get_specs_from_gemini("Samsung Galaxy S24 Ultra")
    print(json.dumps(specs, indent=2, ensure_ascii=False))