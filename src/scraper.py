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
    # Usando o modelo estável 1.5-flash que já deu sinal verde antes
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    prompt = f"""
    Analyze this product: {original_title}
    Description: {original_description}
    Price: {original_price}
    
    Task: Return a JSON object for a professional store. 
    Category must be one of: "Internal Doors", "Front Doors", "Bathroom Doors", "Handles", "Hinges", "Locks", "Cleaning Supplies", "Painting Supplies".
    Format the description in HTML only.
    
    Required JSON Structure:
    {{
      "name": "...",
      "description": "...",
      "category": "...",
      "serviceSlug": "...",
      "color": "...",
      "storeEntries": [{{ "storeName": "B&Q", "price": {original_price if original_price else 0.0}, "inventory": [{{ "size": "Standard", "qty": 1 }}] }}]
    }}
    """
    
    # Template de segurança (Caso a IA erre, usamos este)
    safe_data = {
        "name": original_title,
        "description": f"<p>{original_description}</p>",
        "category": "Hinges" if "hinge" in original_title.lower() else "Internal Doors",
        "serviceSlug": "hinges" if "hinge" in original_title.lower() else "internal-doors",
        "color": "Standard",
        "storeEntries": [{"storeName": "B&Q", "price": float(original_price) if original_price else 0.0, "inventory": [{"size": "Standard", "qty": 1}]}]
    }

    try:
        res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=30)
        if res.status_code == 200:
            ai_text = res.json()['candidates'][0]['content']['parts'][0]['text']
            ai_text = ai_text.strip().removeprefix('```json').removesuffix('```').strip()
            ai_json = json.loads(ai_text)
            
            # MESCLAGEM DE SEGURANÇA: Garante que as chaves do Alvim existem sempre
            for key in safe_data:
                if key not in ai_json:
                    ai_json[key] = safe_data[key]
            return ai_json
    except Exception as e:
        print(f"⚠️ Erro na IA, usando fallback: {e}")
    
    return safe_data

def start_extraction(url):
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        res = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        raw_title = soup.find('h1').text.strip() if soup.find('h1') else "Unknown Product"
        print(f"🔍 RAW TITLE: {raw_title}")
        
        price_tag = soup.find('div', {'data-test-id': 'product-price'})
        raw_price = price_tag.text.replace('€', '').strip() if price_tag else "0.00"
        
        desc_tag = soup.find('div', {'id': 'product-details'})
        raw_desc = desc_tag.text.strip()[:500] if desc_tag else "No desc available."
        
        product_data = generate_optimized_content(raw_title, raw_desc, raw_price)
        
        # Inserção segura do link
        if "storeEntries" in product_data and len(product_data["storeEntries"]) > 0:
            product_data["storeEntries"][0]["link"] = url

        folder_name = "".join(x for x in product_data["name"] if x.isalnum() or x in " -_").strip()
        path = os.path.join(DATA_DIR, folder_name)
        os.makedirs(path, exist_ok=True)

        with open(os.path.join(path, "data.json"), "w", encoding="utf-8") as f:
            json.dump(product_data, f, indent=4, ensure_ascii=False)

        # Download da imagem principal
        og_image = soup.find('meta', property='og:image')
        if og_image:
            img_data = requests.get(og_image['content'].split('?')[0], timeout=10).content
            with open(os.path.join(path, "image_1.jpg"), 'wb') as h: h.write(img_data)
            
        print(f"✅ SUCESSO: {product_data['name']}")
    except Exception as e:
        print(f"❌ ERRO GERAL: {e}")
