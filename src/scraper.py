import os, json, requests, time, random, re
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

def extract_dimensions_from_text(text):
    """Resgate via Python: Busca medidas como 1981x762mm ou 65mm no texto"""
    pattern = r'(\d+x\d+x\d+mm|\d+x\d+mm|\d+mm)'
    match = re.search(pattern, text, re.IGNORECASE)
    return match.group(1) if match else "Standard"

def generate_optimized_content(original_title, original_description, original_price):
    api_key = get_api_key()
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    # Resgate preventivo de dimensões via Python
    detected_size = extract_dimensions_from_text(original_title + " " + original_description)
    
    prompt = f"""
    Transform this product info into a professional JSON for 'Dubliner Handyman' store.
    Title: {original_title}
    Original Price: {original_price}
    
    RULES:
    1. CATEGORY: One of ["Internal Doors", "Front Doors", "Bathroom Doors", "Handles", "Hinges", "Locks", "Cleaning Supplies", "Painting Supplies"].
    2. DESCRIPTION: High-quality HTML paragraphs. Focus on materials and durability.
    3. SIZE: Use '{detected_size}' if found, otherwise extract from text.
    
    Return ONLY JSON:
    {{
      "name": "...", "description": "...", "category": "...", "serviceSlug": "...",
      "color": "...", "storeEntries": [{{ "storeName": "B&Q", "price": 0.0, "inventory": [{{ "size": "...", "qty": 1 }}] }}]
    }}
    """
    try:
        res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=30)
        return json.loads(res.json()['candidates'][0]['content']['parts'][0]['text'].strip().removeprefix('```json').removesuffix('```').strip())
    except:
        # Fallback inteligente com dados já minerados pelo Python
        cat = "Hinges" if "hinge" in original_title.lower() else "Internal Doors"
        return {
            "name": original_title, "description": f"<p>{original_description}</p>",
            "category": cat, "serviceSlug": cat.lower().replace(" ", "-"), "color": "Standard",
            "storeEntries": [{"storeName": "B&Q", "price": float(original_price) if original_price != "0.00" else 0.0, "inventory": [{"size": detected_size, "qty": 1}]}]
        }

def start_extraction(url):
    # Rotação de User-Agents para evitar bloqueio
    agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
        'Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1'
    ]
    
    session = requests.Session()
    session.headers.update({'User-Agent': random.choice(agents), 'Accept-Language': 'en-IE,en-GB;q=0.9,en;q=0.8'})

    try:
        # Simula tempo de leitura humana
        time.sleep(random.uniform(2, 5))
        
        res = session.get(url, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        h1 = soup.find('h1')
        raw_title = h1.text.strip() if h1 else ""
        
        if not raw_title or "techies" in raw_title.lower():
            print("❌ BLOQUEIO: O site detetou o robô. A tentar manobra de evasão...")
            return

        print(f"🔍 MINERANDO: {raw_title}")
        
        price_tag = soup.find('div', {'data-test-id': 'product-price'})
        raw_price = price_tag.text.replace('€', '').strip() if price_tag else "0.00"
        
        desc_tag = soup.find('div', {'id': 'product-details'})
        raw_desc = desc_tag.get_text(separator=" ").strip()[:800] if desc_tag else ""
        
        product_data = generate_optimized_content(raw_title, raw_desc, raw_price)
        product_data["storeEntries"][0]["link"] = url

        folder_name = "".join(x for x in product_data["name"] if x.isalnum() or x in " -_").strip()
        path = os.path.join(DATA_DIR, folder_name)
        os.makedirs(path, exist_ok=True)

        with open(os.path.join(path, "data.json"), "w", encoding="utf-8") as f:
            json.dump(product_data, f, indent=4, ensure_ascii=False)

        print(f"✅ FINALIZADO COM SUCESSO: {product_data['name']}")
    except Exception as e:
        print(f"❌ ERRO CRÍTICO: {e}")
