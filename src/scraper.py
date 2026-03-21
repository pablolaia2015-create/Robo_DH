import os
import json
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
HISTORY_FILE = os.path.join(BASE_DIR, "extracted_links_db.txt")

def get_api_key():
    try:
        import streamlit as st
        if "GOOGLE_API_KEY" in st.secrets:
            return st.secrets["GOOGLE_API_KEY"]
    except ImportError:
        pass
    return os.getenv("GOOGLE_API_KEY")

def generate_optimized_content(original_title, original_description, original_price):
    api_key = get_api_key()
    
    # Fallback structure for Alvim's database
    fallback_data = {
        "name": original_title,
        "description": f"<p>{original_description}</p>",
        "category": "Internal Doors",
        "serviceSlug": "internal-doors",
        "color": "Standard",
        "storeEntries": [{"storeName": "B&Q", "price": float(original_price) if original_price else 0.0, "inventory": [{"size": "Standard", "qty": 1}]}]
    }
    
    if not api_key: return fallback_data

    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key={api_key}"
    
    # NOVO PROMPT: Equilíbrio entre Técnico e Comercial (Sem Markdown)
    prompt = f"""
    You are a high-end interior design copywriter. 
    Transform this product into a premium listing for 'Dubliner Handyman'.

    PRODUCT DATA:
    Title: {original_title}
    Raw Info: {original_description}
    Price: {original_price}
    
    RULES:
    1. 'description': Write 2-3 engaging paragraphs in HTML (<p>, <b>, <ul>, <li>). 
       Focus on how this item improves a home's style and functionality. 
       STRICT: No Markdown asterisks (**).
    2. 'category': Choose exactly one: "Internal Doors", "Front Doors", "Bathroom Doors", "Handles", "Hinges", "Locks", "Cleaning Supplies", "Painting Supplies".
    3. 'serviceSlug': Lowercase version of category (e.g., "internal-doors").
    4. 'storeEntries': 
       - 'price': Numeric float (e.g. 145.00).
       - 'inventory': Extract size dimensions (e.g. "(h)1981mm (w)762mm") and set qty to 1.

    Return ONLY a valid JSON object:
    {{
      "name": "Refined Premium Title",
      "description": "HTML content",
      "category": "...",
      "serviceSlug": "...",
      "color": "Extract color/finish",
      "storeEntries": [{{ "storeName": "B&Q", "price": 0.0, "inventory": [{{ "size": "...", "qty": 1 }}] }}]
    }}
    """
    
    try:
        res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=30)
        if res.status_code == 200:
            ai_text = res.json()['candidates'][0]['content']['parts'][0]['text']
            ai_text = ai_text.strip().removeprefix('```json').removesuffix('```').strip()
            return json.loads(ai_text)
    except:
        pass
    return fallback_data

def is_link_extracted(url):
    if not os.path.exists(HISTORY_FILE): return False
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        return url in f.read().splitlines()

def save_extracted_link(url):
    with open(HISTORY_FILE, "a", encoding="utf-8") as f: f.write(url + "\n")

def start_extraction(url):
    if is_link_extracted(url): return
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        res = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        title = soup.find('h1').text.strip() if soup.find('h1') else "Unknown"
        price = soup.find('div', {'data-test-id': 'product-price'}).text.replace('€', '').strip() if soup.find('div', {'data-test-id': 'product-price'}) else "0.00"
        desc = soup.find('div', {'id': 'product-details'}).text.strip()[:600] if soup.find('div', {'id': 'product-details'}) else ""
        
        product_data = generate_optimized_content(title, desc, price)
        product_data["storeEntries"][0]["link"] = url

        folder_name = "".join(x for x in product_data["name"] if x.isalnum() or x in " -_").strip()
        path = os.path.join(DATA_DIR, folder_name)
        os.makedirs(path, exist_ok=True)

        with open(os.path.join(path, "data.json"), "w", encoding="utf-8") as f:
            json.dump(product_data, f, indent=4, ensure_ascii=False)

        # Image download logic remains the same...
        og_image = soup.find('meta', property='og:image')
        img_urls = [og_image['content'].split('?')[0]] if og_image else []
        img_count = 0
        for src in img_urls:
            img_data = requests.get(src, timeout=10).content
            if len(img_data) > 5000:
                img_count += 1
                with open(os.path.join(path, f"image_{img_count}.jpg"), 'wb') as h: h.write(img_data)
        
        save_extracted_link(url)
        print(f"✅ SAVED: {folder_name}")
    except Exception as e: print(f"❌ ERROR: {e}")
