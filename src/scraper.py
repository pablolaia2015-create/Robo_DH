import os, json, time, random, re
import cloudscraper
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
    Transform this DIY product into a professional JSON.
    Title: {original_title}
    Original Price: {original_price}
    Desc: {original_description}
    
    RULES:
    1. CATEGORY: One of ["Internal Doors", "Front Doors", "Bathroom Doors", "Handles", "Hinges", "Locks", "Cleaning Supplies", "Painting Supplies"].
    2. DESCRIPTION: HTML paragraphs focusing on quality.
    3. INVENTORY: Extract dimensions (e.g. 1981x762mm) from title or text.

    Return ONLY JSON:
    {{
      "name": "...", "description": "...", "category": "...", "serviceSlug": "...",
      "color": "...", "storeEntries": [{{ "storeName": "B&Q", "price": {original_price}, "inventory": [{{ "size": "...", "qty": 1 }}] }}]
    }}
    """
    try:
        import requests
        res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=30)
        return json.loads(res.json()['candidates'][0]['content']['parts'][0]['text'].strip().removeprefix('```json').removesuffix('```').strip())
    except:
        return {"name": original_title, "category": "Internal Doors", "storeEntries": [{"storeName": "B&Q", "price": 0.0, "inventory": [{"size": "Standard", "qty": 1}]}]}

def start_extraction(url):
    # O cloudscraper cria um navegador que resolve desafios de firewall automaticamente
    scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})
    
    try:
        time.sleep(random.uniform(3, 7)) # Pausa para parecer humano
        res = scraper.get(url, timeout=20)
        
        if res.status_code != 200:
            print(f"❌ ERRO DE ACESSO ({res.status_code}): O site bloqueou.")
            return

        soup = BeautifulSoup(res.text, 'html.parser')
        h1 = soup.find('h1')
        raw_title = h1.text.strip() if h1 else ""

        if "techies" in raw_title.lower() or not raw_title:
            print("❌ BLOQUEIO: Página de erro detetada.")
            return

        print(f"🔍 DADOS RECUPERADOS: {raw_title}")
        
        price_tag = soup.find('div', {'data-test-id': 'product-price'})
        raw_price = price_tag.text.replace('€', '').strip() if price_tag else "0.00"
        
        # Tentativa de pegar descrição de forma mais profunda
        desc_tag = soup.find('div', {'id': 'product-details'}) or soup.find('div', {'class': 'product-description'})
        raw_desc = desc_tag.get_text(separator=" ").strip()[:800] if desc_tag else ""
        
        product_data = generate_optimized_content(raw_title, raw_desc, raw_price)
        product_data["storeEntries"][0]["link"] = url
        product_data["serviceSlug"] = product_data["category"].lower().replace(" ", "-")

        folder_name = "".join(x for x in product_data["name"] if x.isalnum() or x in " -_").strip()
        path = os.path.join(DATA_DIR, folder_name)
        os.makedirs(path, exist_ok=True)

        with open(os.path.join(path, "data.json"), "w", encoding="utf-8") as f:
            json.dump(product_data, f, indent=4, ensure_ascii=False)
            
        print(f"✅ SUCESSO: {product_data['name']}")
    except Exception as e:
        print(f"❌ FALHA CRÍTICA: {e}")
