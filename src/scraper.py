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
    
    prompt = f"Transform this into a product JSON for a DIY store: {original_title}. Desc: {original_description}. Price: {original_price}. Output JSON only."
    
    try:
        res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=30)
        if res.status_code == 200:
            ai_text = res.json()['candidates'][0]['content']['parts'][0]['text']
            return json.loads(ai_text.strip().removeprefix('```json').removesuffix('```').strip())
    except: pass
    return {"name": original_title, "category": "General", "storeEntries": [{"storeName": "B&Q", "price": 0.0, "inventory": [{"size": "Standard", "qty": 1}]}]}

def start_extraction(url):
    # User-Agent mais 'humano' para tentar passar pelo bloqueio
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/00.1'
    }
    try:
        res = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        raw_title = soup.find('h1').text.strip() if soup.find('h1') else "Unknown"
        
        # 🛡️ ESCUDO: Se o site nos der a página de 'techies', paramos aqui!
        if "techies" in raw_title.lower() or "sorry" in raw_title.lower():
            print("❌ BLOQUEIO DETETADO: O site da B&Q bloqueou o robô. Tente novamente mais tarde.")
            return

        print(f"🔍 RAW TITLE: {raw_title}")
        
        price_tag = soup.find('div', {'data-test-id': 'product-price'})
        raw_price = price_tag.text.replace('€', '').strip() if price_tag else "0.00"
        
        desc_tag = soup.find('div', {'id': 'product-details'})
        raw_desc = desc_tag.text.strip()[:500] if desc_tag else "No desc."
        
        product_data = generate_optimized_content(raw_title, raw_desc, raw_price)
        product_data["storeEntries"][0]["link"] = url

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
