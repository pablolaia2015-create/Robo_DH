import os, json, time, random, re
import cloudscraper
import requests
import shutil
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# --- ARMAS PARA FURAR O CLOUDFLARE E LER IMAGENS ---
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from PIL import Image

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
MEMORIA_DIR = os.path.join(BASE_DIR, "memoria")
os.makedirs(MEMORIA_DIR, exist_ok=True)

LINKS_FILE = os.path.join(MEMORIA_DIR, "processed_links.txt")
CATEGORIES_FILE = os.path.join(MEMORIA_DIR, "categories.txt")

def load_categories():
    if os.path.exists(CATEGORIES_FILE):
        with open(CATEGORIES_FILE, "r", encoding="utf-8") as f:
            cats = [line.strip() for line in f if line.strip()]
            if cats: return cats
    return ["Internal Doors", "External Doors", "Doors & Hardware", "Handles", "Hinges", "Painting", "Flooring", "General"]

def save_category(new_cat):
    cats = load_categories()
    if new_cat not in cats:
        with open(CATEGORIES_FILE, "a", encoding="utf-8") as f:
            f.write(new_cat + "\n")

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

def extract_all_images(soup):
    images = []
    try:
        for schema in soup.find_all('script', type='application/ld+json'):
            data = json.loads(schema.string)
            items = data if isinstance(data, list) else [data]
            for item in items:
                if item.get('@type') == 'Product' and item.get('image'):
                    img = item.get('image')
                    images.extend(img if isinstance(img, list) else [img])
    except: pass
    if not images:
        og = soup.find('meta', property='og:image')
        if og and og.get('content'): images.append(og['content'])
    return list(dict.fromkeys([i for i in images if isinstance(i, str)]))

def get_smart_title(soup):
    h1 = soup.find('h1')
    if h1 and h1.text.strip(): return h1.text.strip()
    og = soup.find('meta', property='og:title')
    if og and og.get('content'): return og['content'].split(' - ')[0].strip()
    return soup.title.text.split(' - ')[0].strip() if soup.title else "Produto Sem Nome"

def extract_all_dimensions(text):
    m = re.findall(r'(\d+(?:\.\d+)?\s*(?:mm|cm|m)(?:\s*x\s*\d+(?:\.\d+)?\s*(?:mm|cm|m))?)', text, re.I)
    return " / ".join(dict.fromkeys([x.strip() for x in m])) if m else "Standard"

def get_smart_sizes_bs4(soup):
    sizes = []
    for sel in ['.swatch-option.text','.size-selection','select[id*="attribute"] option','select[name*="size"] option','.product-options-wrapper select option']:
        for el in soup.select(sel):
            t = el.get_text(strip=True)
            if t and not any(w in t.lower() for w in ["choose","select","selecione","escolha"]):
                sizes.append(t)
        if sizes: break
    return list(dict.fromkeys(sizes))

def generate_optimized_content(title, desc, price, existing_categories, store_name, product_url, lista_tamanhos=None):
    api_key = os.getenv("GOOGLE_API_KEY")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    size_from_title = extract_all_dimensions(title + " " + desc)
    
    try: price_float = float(str(price).replace(',', '.'))
    except: price_float = 0.0
    
    cats_str = ", ".join(f'"{c}"' for c in existing_categories)
    tamanhos_str = ", ".join(lista_tamanhos) if lista_tamanhos else "NO SIZES FOUND"
    fallback_inventory = [{"size": t, "qty": 1} for t in lista_tamanhos] if lista_tamanhos else [{"size": size_from_title, "qty": 1}]
    idioma = "PORTUGUESE (Portugal). Output MUST be in Portuguese." if ".pt" in product_url or store_name == "Leroy Merlin" else "ENGLISH. Output MUST be in English."

    prompt = f"""
    You are an expert e-commerce catalog manager.
    Raw Title: {title}
    Raw Description: {desc}
    Language Rule: {idioma}
    
    TASKS:
    1. Clean Title: Remove generic measurements, keep model name.
    2. Dynamic Category: Check if it fits in [{cats_str}]. If not, INVENT a new specific 1-2 word category.
    3. Color: Extract color/finish. Or "N/A".
    4. Sizes: Found sizes: [{tamanhos_str}]. Create inventory entry for EACH size. If NONE, use extracted size or "Standard".
    5. Description: Professional plain text.
    
    Return EXACT JSON:
    {{
        "name": "<Cleaned Title>",
        "description": "<Plain text description>",
        "category": "<Category>",
        "color": "<Color>",
        "storeEntries": [
            {{
                "storeName": "{store_name}",
                "price": {price_float},
                "link": "{product_url}",
                "inventory": [ {{ "size": "<Size>", "qty": 1 }} ]
            }}
        ]
    }}
    """
    
    fallback_data = {
        "name": re.sub(r'(?i)(\(?[hwdt]\)?\s*)?\d+(?:mm|cm)x?|x\d+(?:mm|cm)', '', title).strip(',- '),
        "description": f"Premium quality {title}.",
        "category": "General", "color": "N/A",
        "storeEntries": [{"storeName": store_name, "price": price_float, "link": product_url, "inventory": fallback_inventory}]
    }
    
    try:
        time.sleep(2)
        res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=30)
        if res.status_code == 200 and 'candidates' in res.json():
            ai_text = res.json()['candidates'][0]['content']['parts'][0]['text']
            cleaned_json = ai_text.strip().removeprefix('```json').removesuffix('```').strip()
            data = json.loads(cleaned_json)
            data["description"] = re.sub(r'<[^>]+>', '', data["description"])
            return data
    except Exception as e:
        print(f"⚠️ Erro na IA: {e}")
    return fallback_data

def extract_with_real_browser(url, store_name):
    print(f"🤖 FATO MECÂNICO ATIVO para a segurança da {store_name}...")
    options = uc.ChromeOptions()
    options.add_argument("--window-size=1920,1080")
    
    driver = uc.Chrome(options=options, version_main=148)
    
    try:
        driver.get(url)
        time.sleep(15) 
        
        try: driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
        except: pass
        
        try: title = driver.find_element(By.CSS_SELECTOR, "h1.page-title span, h1, .product-title").get_attribute("textContent").strip()
        except: title = driver.title
        
        browser_price = None
        for _ in range(10):
            try:
                el = driver.find_element(By.CSS_SELECTOR, '.price-wrapper .price, span.price, .a-price .a-offscreen, [data-cerberus="ELEM_PRIX"], [data-test-id="product-price"]')
                m = re.search(r'(\d+[\.,]\d+)', el.get_attribute("textContent") or el.text)
                if m: 
                    browser_price = m.group(1).replace(',', '.')
                    break
            except: time.sleep(1)
        
        fotos = []
        for sel in ['.product-image-photo','.fotorama__img','picture img','[data-testid="main-image"]','.slick-slide img']:
            for img in driver.find_elements(By.CSS_SELECTOR, sel):
                src = img.get_attribute('data-old-hires') or img.get_attribute('src')
                if src and 'data:image' not in src and 'svg' not in src.lower(): fotos.append(src)
        
        fotos = list(dict.fromkeys(fotos))
        html = driver.page_source
        
        return title, fotos, html, None, [], browser_price
    finally:
        driver.quit()

def start_extraction(url):
    if os.path.exists(LINKS_FILE) and url in open(LINKS_FILE, encoding="utf-8").read():
        print("🛑 Link já extraído!")
        return

    sites_fato_mecanico = ["leroymerlin.pt", "tjomahony.ie", "prolinehardware.ie", "woodies.ie", "amazon.", "diy.ie", "diy.com"]
    usar_selenium = any(s in url.lower() for s in sites_fato_mecanico)

    store_name = "Loja"
    if "woodies" in url: store_name = "Woodies"
    elif "amazon" in url: store_name = "Amazon"
    elif "diy" in url: store_name = "B&Q"
    elif "leroymerlin" in url: store_name = "Leroy Merlin"
    elif "prolinehardware" in url: store_name = "Proline Hardware"
    else:
        try: store_name = url.split('//')[1].split('/')[0].replace('www.','').split('.')[0].capitalize()
        except: pass

    print(f"🛒 {store_name} | Fato Mecânico: {'SIM' if usar_selenium else 'NÃO'}")

    lista_tamanhos = []
    browser_price = None

    if usar_selenium:
        raw_title, fotos_browser, html_content, _, lista_tamanhos, browser_price = extract_with_real_browser(url, store_name)
        soup = BeautifulSoup(html_content, 'html.parser')
        lista_fotos = list(dict.fromkeys(fotos_browser + extract_all_images(soup)))
    else:
        scraper = cloudscraper.create_scraper()
        res = scraper.get(url, timeout=25)
        soup = BeautifulSoup(res.text, 'html.parser')
        raw_title = get_smart_title(soup)
        lista_fotos = extract_all_images(soup)
        lista_tamanhos = get_smart_sizes_bs4(soup)

    if any(w in raw_title.lower() for w in ["404", "not found", "não encontrada"]):
        print("🛑 ALERTA: A página não existe!"); return

    # --- LÓGICA DE PREÇOS ---
    if store_name == "Proline Hardware": raw_price = "0.00"
    elif browser_price: raw_price = browser_price
    else:
        raw_price = extract_price_from_schema(soup)
        if not raw_price:
            pm = re.search(r'"price":\s?"?(\d+[\.,]?\d*)"?', str(soup))
            raw_price = pm.group(1).replace(',', '.') if pm else "0.00"

    raw_desc = raw_title
    desc_tag = soup.find('div', {'id': 'product-details'}) or soup.find('meta', property='og:description')
    if desc_tag: raw_desc = desc_tag.get('content') or desc_tag.get_text(strip=True)

    # --- CHAMA A INTELIGÊNCIA E CRIA O DATA.JSON (A PEÇA QUE FALTAVA!) ---
    current_cats = load_categories()
    product_data = generate_optimized_content(raw_title, raw_desc, raw_price, current_cats, store_name, url, lista_tamanhos)
    
    if product_data.get("category") not in current_cats: 
        save_category(product_data.get("category", "General"))

    path = os.path.join(DATA_DIR, "".join(c for c in product_data["name"] if c.isalnum() or c in " -_").strip()[:60])
    os.makedirs(path, exist_ok=True)

    with open(os.path.join(path, "data.json"), "w", encoding="utf-8") as f:
        json.dump(product_data, f, indent=4, ensure_ascii=False)

    # --- DOWNLOAD COM FILTRO PIL (A TUA GRANDE MELHORIA!) ---
    dl = cloudscraper.create_scraper()
    count = 1
    for img_url in lista_fotos:
        if count > 5: break
        if img_url.startswith('//'): img_url = 'https:' + img_url
        elif img_url.startswith('/'): img_url = "https://" + url.split('/')[2] + img_url
        
        try:
            r = dl.get(img_url, timeout=15)
            if 'text/html' in r.headers.get('Content-Type','').lower(): continue
            tmp = os.path.join(path, f"foto_{count}.jpg")
            with open(tmp, 'wb') as f: f.write(r.content)
            
            if os.path.getsize(tmp) < 2048: 
                os.remove(tmp); continue
                
            try:
                with Image.open(tmp) as im: im.verify()
            except: 
                os.remove(tmp); continue
                
            print(f"✅ Foto {count} guardada!")
            count += 1
        except Exception as e:
            pass

    with open(LINKS_FILE, "a", encoding="utf-8") as f: f.write(url + "\n")
    print(f"🚀 SUCESSO: {product_data['name']} | €{raw_price}")