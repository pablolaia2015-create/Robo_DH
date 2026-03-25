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

def extract_main_image(soup):
    og_image = soup.find('meta', property='og:image')
    if og_image and og_image.get('content'): return og_image['content']
    try:
        schemas = soup.find_all('script', type='application/ld+json')
        for schema in schemas:
            data = json.loads(schema.string)
            items = data if isinstance(data, list) else [data]
            for item in items:
                if item.get('@type') == 'Product' and item.get('image'):
                    img = item.get('image')
                    return img[0] if isinstance(img, list) else img
    except: pass
    return None

def extract_all_dimensions(text):
    pattern = r'(\d+mm)'
    matches = re.findall(pattern, text, re.IGNORECASE)
    return " x ".join(matches) if matches else "Standard"

def generate_optimized_content(title, desc, price):
    api_key = os.getenv("GOOGLE_API_KEY")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    size = extract_all_dimensions(title + " " + desc)
    
    try:
        price_float = float(price.replace(',', '.')) if price else 0.0
    except:
        price_float = 0.0

    # MOLDE EXATO DA API DO ALVIM (TEXTO LIMPO, SEM HTML)
    prompt = f"""
    You are a professional e-commerce specialist.
    Raw Title: {title}
    Raw Price: {price}
    Raw Description: {desc}
    
    Return ONLY a valid JSON object matching EXACTLY this structure (do not add markdown blocks like ```json).
    CRITICAL INSTRUCTION FOR DESCRIPTION: Use PLAIN TEXT ONLY. DO NOT USE ANY HTML TAGS (no <p>, no <b>, no <ul>). Use standard newline characters (\\n) for paragraphs.
    {{
        "name": "{title}",
        "description": "Professional plain text description here.\\n\\nSecond paragraph here.",
        "category": "Internal Doors",
        "color": "Standard",
        "storeEntries": [
            {{
                "storeName": "B&Q",
                "price": {price_float},
                "inventory": [
                    {{
                        "size": "{size}",
                        "qty": 1
                    }}
                ]
            }}
        ]
    }}
    """
    
    fallback_data = {
        "name": title,
        "description": f"Premium quality {title} for your home projects.\n\nIdeal for upgrades and renovations.",
        "category": "Internal Doors",
        "color": "Standard",
        "storeEntries": [{"storeName": "B&Q", "price": price_float, "inventory": [{"size": size, "qty": 1}]}]
    }

    try:
        import requests
        time.sleep(2)
        res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=30)
        
        if res.status_code == 200 and 'candidates' in res.json():
            ai_text = res.json()['candidates'][0]['content']['parts'][0]['text']
            cleaned_json = ai_text.strip().removeprefix('```json').removesuffix('```').strip()
            
            # Limpeza dupla: garante que se a IA teimar em usar HTML, nós apagamos!
            data = json.loads(cleaned_json)
            data["description"] = re.sub(r'<[^>]+>', '', data["description"])
            return data
        else:
            return fallback_data
    except Exception:
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
        # O backend do Alvim exige o link no storeEntries
        product_data["storeEntries"][0]["link"] = url

        path = os.path.join(DATA_DIR, "".join(x for x in product_data["name"] if x.isalnum() or x in " -_").strip())
        os.makedirs(path, exist_ok=True)
        
        with open(os.path.join(path, "data.json"), "w", encoding="utf-8") as f:
            json.dump(product_data, f, indent=4, ensure_ascii=False)
            
        img_url = extract_main_image(soup)
        if img_url:
            if img_url.startswith('//'): img_url = 'https:' + img_url
            img_data = scraper.get(img_url, timeout=15).content
            with open(os.path.join(path, "foto_1.jpg"), 'wb') as handler:
                handler.write(img_data)
            print("📸 Fotografia guardada!")

        print(f"✅ SUCESSO COMPLETO (TEXTO LIMPO): {product_data['name']} | €{raw_price}")
    except Exception as e: print(f"❌ FALHA: {e}")