import os, json, requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
HISTORY_FILE = os.path.join(BASE_DIR, "extracted_links_db.txt")

def get_api_key():
    try:
        import streamlit as st
        return st.secrets["GOOGLE_API_KEY"] if "GOOGLE_API_KEY" in st.secrets else os.getenv("GOOGLE_API_KEY")
    except: return os.getenv("GOOGLE_API_KEY")

def generate_optimized_content(original_title, original_description, original_price):
    api_key = get_api_key()
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key={api_key}"
    
    # Prompt mais rígido para evitar inventar portas onde há dobradiças
    prompt = f"""
    Analyze this raw e-commerce data carefully:
    Title: {original_title}
    Description: {original_description}
    Price: {original_price}
    
    TASK:
    1. Determine if this is a DOOR or an ACCESSORY (Hinge, Handle, Lock).
    2. 'category': Must be one of: "Internal Doors", "Front Doors", "Bathroom Doors", "Handles", "Hinges", "Locks", "Cleaning Supplies", "Painting Supplies".
    3. 'name': Create a professional title. DO NOT call it a "Door" if the title says "Hinge" or "Handle".
    4. 'description': Use ONLY HTML tags (<p>, <b>, <ul>, <li>). Focus ONLY on the actual product features.
    5. 'inventory': Extract the REAL dimensions of the item (e.g. 100mm, 75mm). DO NOT use door sizes (1981x762) for accessories.

    Return ONLY a valid JSON object.
    """
    
    try:
        res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=30)
        if res.status_code == 200:
            ai_text = res.json()['candidates'][0]['content']['parts'][0]['text']
            return json.loads(ai_text.strip().removeprefix('```json').removesuffix('```').strip())
    except: pass
    return {"name": original_title, "category": "Uncategorized", "storeEntries": [{"storeName": "B&Q", "price": original_price, "inventory": [{"size": "N/A", "qty": 1}]}]}

def start_extraction(url):
    # Verificação de histórico desativada temporariamente para permitir RE-EXTRAÇÃO durante testes
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        res = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # LOG DE DIAGNÓSTICO: Mostra o que o robô realmente "leu" no terminal
        raw_title = soup.find('h1').text.strip() if soup.find('h1') else "Unknown"
        print(f"🔍 RAW TITLE FOUND: {raw_title}")
        
        raw_price = soup.find('div', {'data-test-id': 'product-price'}).text.replace('€', '').strip() if soup.find('div', {'data-test-id': 'product-price'}) else "0.00"
        raw_desc = soup.find('div', {'id': 'product-details'}).text.strip()[:500] if soup.find('div', {'id': 'product-details'}) else "No description found (Blocked?)"
        
        product_data = generate_optimized_content(raw_title, raw_desc, raw_price)
        product_data["storeEntries"][0]["link"] = url

        folder_name = "".join(x for x in product_data["name"] if x.isalnum() or x in " -_").strip()
        path = os.path.join(DATA_DIR, folder_name)
        os.makedirs(path, exist_ok=True)

        with open(os.path.join(path, "data.json"), "w", encoding="utf-8") as f:
            json.dump(product_data, f, indent=4, ensure_ascii=False)

        # Download de imagens melhorado
        og_image = soup.find('meta', property='og:image')
        if og_image:
            img_data = requests.get(og_image['content'].split('?')[0], timeout=10).content
            with open(os.path.join(path, "main_image.jpg"), 'wb') as h: h.write(img_data)
            
        print(f"✅ FINALIZED: {product_data['name']} categorized as {product_data['category']}")
    except Exception as e: print(f"❌ ERROR: {e}")
