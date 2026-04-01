import os, json, time, random, re
import cloudscraper
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()
# CAMINHOS BASE
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
LINKS_FILE = os.path.join(BASE_DIR, "processed_links.txt")
CATEGORIES_FILE = os.path.join(BASE_DIR, "categories.txt")

# --- FUNÇÕES DE MEMÓRIA DE CATEGORIAS ---
def load_categories():
    if os.path.exists(CATEGORIES_FILE):
        with open(CATEGORIES_FILE, "r", encoding="utf-8") as f:
            cats = [line.strip() for line in f if line.strip()]
            if cats: return cats
    return ["Internal Doors", "External Doors", "Doors & Hardware", "Handles", "Hinges", "Painting", "General"]

def save_category(new_cat):
    cats = load_categories()
    if new_cat not in cats:
        with open(CATEGORIES_FILE, "a", encoding="utf-8") as f:
            f.write(new_cat + "\n")
# ----------------------------------------------

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

# ATENÇÃO: Agora a função recebe o store_name dinâmico!
def generate_optimized_content(title, desc, price, existing_categories, store_name):
    api_key = os.getenv("GOOGLE_API_KEY")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    size = extract_all_dimensions(title + " " + desc)
    
    try:
        price_float = float(price.replace(',', '.')) if price else 0.0
    except:
        price_float = 0.0

    cats_str = ", ".join(f'"{c}"' for c in existing_categories)

    prompt = f"""
    You are an expert e-commerce catalog manager.
    Raw Title: {title}
    Raw Description: {desc}
    
    TASKS:
    1. Clean Title: Remove generic measurements from the title to make it elegant, BUT keep essential model names. 
    2. Dynamic Category with Memory:
       Here is the list of CURRENTLY EXISTING categories in our store: [{cats_str}]
       - RULE A: You MUST try to categorize the product into one of these existing categories if it makes logical sense.
       - RULE B: IF AND ONLY IF the product absolutely does not fit ANY of the existing categories, you may create a NEW, simple, 1-2 word category (e.g., "Sealants", "PPE", "Locks"). ALWAYS use English plural where applicable.
    3. Identify Size/Volume: Extract the size intelligently based on the product. (e.g., "1981mm x 838mm", "2Ltr", "300ml"). If no size makes sense, return "Standard".
    4. Identify Color/Finish: You MUST extract the primary color or finish. Actively search the title and description for words like White, Black, Clear, Chrome, Brass, Pine, Oak, Grey, Silver, Gold, etc. If you find a color word, output ONLY that word (e.g., "White"). ONLY use "Standard" if absolutely no color is mentioned anywhere.
    5. Rewrite Description: Create a UNIQUE, highly engaging, and professional plain text description. DO NOT use HTML tags. Use double line breaks (\\n\\n) for paragraphs.
    
    Return ONLY a valid JSON object matching EXACTLY this structure (no markdown blocks):
    {{
        "name": "<Cleaned Title>",
        "description": "<Your plain text description>",
        "category": "<The chosen existing category OR the newly created one>",
        "color": "<The extracted color/finish>",
        "storeEntries": [
            {{
                "storeName": "{store_name}",
                "price": {price_float},
                "inventory": [
                    {{
                        "size": "<The extracted size/volume>",
                        "qty": 1
                    }}
                ]
            }}
        ]
    }}
    """
    
    fallback_data = {
        "name": re.sub(r'(?i)(\(?[hwdt]\)?\s*)?\d+(?:mm|cm)x?|x\d+(?:mm|cm)', '', title).strip(' ,-'),
        "description": f"Premium quality {title} for your home projects.\n\nIdeal for professional installations.",
        "category": "General",
        "color": "Standard",
        "storeEntries": [{"storeName": store_name, "price": price_float, "inventory": [{"size": size, "qty": 1}]}]
    }

    try:
        import requests
        time.sleep(2)
        res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=30)
        
        if res.status_code == 200 and 'candidates' in res.json():
            ai_text = res.json()['candidates'][0]['content']['parts'][0]['text']
            cleaned_json = ai_text.strip().removeprefix('```json').removesuffix('```').strip()
            
            data = json.loads(cleaned_json)
            data["description"] = re.sub(r'<[^>]+>', '', data["description"])
            return data
        else:
            return fallback_data
    except Exception:
        return fallback_data

def start_extraction(url):
    if os.path.exists(LINKS_FILE):
        with open(LINKS_FILE, "r", encoding="utf-8") as f:
            if url in f.read():
                print(f"\n🛑 AVISO: O link já foi extraído anteriormente!")
                print("Ignorando a extração para não sujar o sistema.\n")
                return

    # --- O ROUTER: DETETAR QUAL É A LOJA ---
    if "diy.ie" in url or "diy.com" in url:
        store_name = "B&Q"
    elif "screwfix.ie" in url:
        store_name = "Screwfix"
    elif "woodworkers.ie" in url:
        store_name = "WoodWorkers"
    else:
        store_name = "Desconhecida"
    
    print(f"🛒 Loja detetada pelo Router: {store_name}")
    # ----------------------------------------

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

        current_cats = load_categories()
        # Passa o nome da loja para a IA!
        product_data = generate_optimized_content(raw_title, raw_desc, raw_price, current_cats, store_name)
        
        ai_cat = product_data.get("category", "General")
        if ai_cat not in current_cats:
            save_category(ai_cat)
            print(f"🆕 A IA aprendeu e guardou uma categoria NOVA: '{ai_cat}'")

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

        print(f"✅ SUCESSO COMPLETO: {product_data['name']} | €{raw_price} | Loja: {store_name}")
        
        with open(LINKS_FILE, "a", encoding="utf-8") as f:
            f.write(url + "\n")

    except Exception as e: print(f"❌ FALHA: {e}")