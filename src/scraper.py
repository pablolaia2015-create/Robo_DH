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
    
    # Prompt reforçado para análise profunda do título
    prompt = f"""
    ROLE: Professional E-commerce Content Creator.
    DATA TO ANALYZE:
    Title: {original_title}
    Description: {original_description}
    Price: {original_price}
    
    INSTRUCTIONS:
    1. CATEGORY: You MUST choose exactly one from this list: ["Internal Doors", "Front Doors", "Bathroom Doors", "Handles", "Hinges", "Locks", "Cleaning Supplies", "Painting Supplies"].
    - If title mentions 'hinge', category IS 'Hinges'.
    - If title mentions 'handle', category IS 'Handles'.
    - If title mentions 'lock' or 'latch', category IS 'Locks'.
    2. DESCRIPTION: Write a professional HTML description (<p>, <b>, <ul>, <li>). If the original description is empty, use the title to create a benefits-focused text.
    3. INVENTORY: Extract dimensions from the title (e.g., '65mm', '1981x762mm').
    4. PRICE: Must be a number. Current raw price: {original_price}.

    OUTPUT: Only valid JSON.
    """
    
    try:
        res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=30)
        if res.status_code == 200:
            ai_text = res.json()['candidates'][0]['content']['parts'][0]['text']
            return json.loads(ai_text.strip().removeprefix('```json').removesuffix('```').strip())
    except Exception as e:
        print(f"⚠️ AI logic failed: {e}")
    
    # Template dinâmico de segurança mais inteligente
    cat = "Hinges" if "hinge" in original_title.lower() else "Internal Doors"
    return {
        "name": original_title,
        "description": f"<p>Premium quality {original_title} for your home projects.</p>",
        "category": cat,
        "serviceSlug": cat.lower().replace(" ", "-"),
        "color": "Standard",
        "storeEntries": [{"storeName": "B&Q", "price": float(original_price) if original_price and original_price != "0.00" else 0.0, "inventory": [{"size": "Standard", "qty": 1}]}]
    }

def start_extraction(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    try:
        res = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        h1 = soup.find('h1')
        raw_title = h1.text.strip() if h1 else ""
        
        if not raw_title or "techies" in raw_title.lower():
            print("❌ ACESSO NEGADO: O site bloqueou o robô. Tente outro link ou aguarde.")
            return

        print(f"🔍 ANALISANDO: {raw_title}")
        
        # Tenta pegar o preço em locais alternativos se o principal falhar
        price_tag = soup.find('div', {'data-test-id': 'product-price'})
        raw_price = price_tag.text.replace('€', '').strip() if price_tag else "0.00"
        
        desc_tag = soup.find('div', {'id': 'product-details'})
        raw_desc = desc_tag.get_text(separator=" ").strip()[:800] if desc_tag else ""
        
        product_data = generate_optimized_content(raw_title, raw_desc, raw_price)
        product_data["storeEntries"][0]["link"] = url
        
        # Garante que o serviceSlug existe
        if "category" in product_data:
            product_data["serviceSlug"] = product_data["category"].lower().replace(" ", "-")

        folder_name = "".join(x for x in product_data["name"] if x.isalnum() or x in " -_").strip()
        path = os.path.join(DATA_DIR, folder_name)
        os.makedirs(path, exist_ok=True)

        with open(os.path.join(path, "data.json"), "w", encoding="utf-8") as f:
            json.dump(product_data, f, indent=4, ensure_ascii=False)

        # Download da imagem
        og_image = soup.find('meta', property='og:image')
        if og_image:
            img_data = requests.get(og_image['content'].split('?')[0], timeout=10).content
            with open(os.path.join(path, "image_1.jpg"), 'wb') as h: h.write(img_data)
            
        print(f"✅ SUCESSO: {product_data['name']}")
    except Exception as e:
        print(f"❌ ERRO: {e}")
