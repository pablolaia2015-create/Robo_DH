import os, json, requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

def get_api_key():
    try:
        import streamlit as st
        return st.secrets["GOOGLE_API_KEY"] if "GOOGLE_API_KEY" in st.secrets else os.getenv("GOOGLE_API_KEY")
    except: return os.getenv("GOOGLE_API_KEY")

def generate_optimized_content(original_title, original_description, original_price):
    api_key = get_api_key()
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    prompt = f"""
    You are a professional e-commerce specialist for 'Dubliner Handyman'.
    Analyze this product:
    Title: {original_title}
    Description: {original_description}
    Price: {original_price}
    
    RULES:
    1. 'category': MUST be one of: "Internal Doors", "Front Doors", "Bathroom Doors", "Handles", "Hinges", "Locks", "Cleaning Supplies", "Painting Supplies".
    2. 'description': Use ONLY HTML (<p>, <b>, <ul>, <li>). NO Markdown.
    3. 'inventory': Extract the REAL dimensions (e.g. "(H)1946mm (W)750mm") and set qty to 1.
    4. 'price': Return the price as a float (e.g. 145.00). Use the price provided: {original_price}.

    Return ONLY a valid JSON object.
    """
    
    try:
        res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=30)
        if res.status_code == 200:
            ai_text = res.json()['candidates'][0]['content']['parts'][0]['text']
            return json.loads(ai_text.strip().removeprefix('```json').removesuffix('```').strip())
    except: pass
    
    # Fallback caso a IA falhe
    return {
        "name": original_title,
        "description": f"<p>{original_description}</p>",
        "category": "Internal Doors",
        "serviceSlug": "internal-doors",
        "color": "Standard",
        "storeEntries": [{"storeName": "B&Q", "price": float(original_price) if original_price else 0.0, "inventory": [{"size": "Standard", "qty": 1}]}]
    }

def start_extraction(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        res = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        h1 = soup.find('h1')
        raw_title = h1.text.strip() if h1 else ""
        
        # Detetor de bloqueio
        if "techies" in raw_title.lower() or not raw_title:
            print("❌ BLOQUEIO: O site não entregou os dados. Tente novamente.")
            return

        print(f"🔍 EXTRAINDO: {raw_title}")
        
        price_tag = soup.find('div', {'data-test-id': 'product-price'})
        raw_price = price_tag.text.replace('€', '').strip() if price_tag else "0.00"
        
        desc_tag = soup.find('div', {'id': 'product-details'})
        raw_desc = desc_tag.text.strip()[:600] if desc_tag else ""
        
        product_data = generate_optimized_content(raw_title, raw_desc, raw_price)
        product_data["storeEntries"][0]["link"] = url
        product_data["serviceSlug"] = product_data["category"].lower().replace(" ", "-")

        folder_name = "".join(x for x in product_data["name"] if x.isalnum() or x in " -_").strip()
        path = os.path.join(DATA_DIR, folder_name)
        os.makedirs(path, exist_ok=True)

        with open(os.path.join(path, "data.json"), "w", encoding="utf-8") as f:
            json.dump(product_data, f, indent=4, ensure_ascii=False)

        og_image = soup.find('meta', property='og:image')
        if og_image:
            img_data = requests.get(og_image['content'].split('?')[0], timeout=10).content
            with open(os.path.join(path, "image_1.jpg"), 'wb') as h: h.write(img_data)
            
        print(f"✅ SUCESSO: {product_data['name']}")
    except Exception as e:
        print(f"❌ ERRO: {e}")
