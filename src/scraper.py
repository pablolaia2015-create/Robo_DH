import os, json, time, random, re
import cloudscraper
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

def extract_price_from_schema(soup):
    try:
        schemas = soup.find_all('script', type='application/ld+json')
        for schema in schemas:
            data = json.loads(schema.string)
            items = data if isinstance(data, list) else [data]
            for item in items:
                if item.get('@type') == 'Product' or 'offers' in item:
                    offers = item.get('offers')
                    if isinstance(offers, list): offers = offers[0]
                    price = offers.get('price')
                    if price: return str(price)
    except: pass
    return None

def extract_all_dimensions(text):
    pattern = r'(\d+mm)'
    matches = re.findall(pattern, text, re.IGNORECASE)
    return " x ".join(matches) if matches else "Standard"

def generate_optimized_content(title, desc, price):
    api_key = os.getenv("GOOGLE_API_KEY")
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={api_key}"
    size = extract_all_dimensions(title + " " + desc)
    
    prompt = f"""
    You are a professional e-commerce specialist.
    Title: {title}
    Price: {price}
    Desc: {desc}
    
    Return ONLY a valid JSON object with these exact keys: "name", "description" (HTML formatting), "category" (Internal Doors), "serviceSlug" (internal-doors), "color" (Standard), "storeEntries" (with price {price} and size '{size}').
    """
    
    # O Fallback super seguro caso a IA da Google falhe por limite de uso
    fallback_data = {
        "name": title,
        "description": f"<p>Premium quality {title} for your home projects.</p>",
        "category": "Internal Doors",
        "serviceSlug": "internal-doors",
        "color": "Standard",
        "storeEntries": [{"storeName": "B&Q", "price": float(price) if price else 0.0, "inventory": [{"size": size, "qty": 1}]}]
    }

    try:
        import requests
        time.sleep(2) # Pausa de segurança para não ser bloqueado pela Google
        res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=30)
        
        if res.status_code == 200 and 'candidates' in res.json():
            ai_text = res.json()['candidates'][0]['content']['parts'][0]['text']
            return json.loads(ai_text.strip().removeprefix('```json').removesuffix('```').strip())
        else:
            print("⚠️ A Google (Gemini) não respondeu bem. Usando Fallback.")
            return fallback_data
    except Exception as e:
        print(f"⚠️ Erro de comunicação com a IA. Usando Fallback.")
        return fallback_data

def start_extraction(url):
    scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows'})
    try:
        time.sleep(random.uniform(2, 5))
        res = scraper.get(url, timeout=25)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        h1 = soup.find('h1')
        raw_title = h1.text.strip() if h1 else ""
        
        raw_price = extract_price_from_schema(soup)
        if not raw_price or raw_price == "75":
             price_match = re.search(r'"price":\s?"(\d+[\.,]?\d*)"', res.text)
             raw_price = price_match.group(1) if price_match else "0.00"

        desc_tag = soup.find('div', {'id': 'product-details'}) or soup.find('meta', {'name': 'description'})
        raw_desc = desc_tag.get_text() if hasattr(desc_tag, 'get_text') else ""

        product_data = generate_optimized_content(raw_title, raw_desc, raw_price)
        product_data["storeEntries"][0]["link"] = url

        path = os.path.join(DATA_DIR, "".join(x for x in product_data["name"] if x.isalnum() or x in " -_").strip())
        os.makedirs(path, exist_ok=True)
        with open(os.path.join(path, "data.json"), "w", encoding="utf-8") as f:
            json.dump(product_data, f, indent=4, ensure_ascii=False)
        print(f"✅ SUCESSO COMPLETO: {product_data['name']} | €{raw_price}")
    except Exception as e: print(f"❌ FALHA: {e}")

