import os, json, time, random, re
import cloudscraper
import requests
import shutil
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from io import BytesIO

# --- TOOLS TO BYPASS CLOUDFLARE AND READ IMAGES ---
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from PIL import Image

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
MEMORY_DIR = os.path.join(BASE_DIR, "memory")
os.makedirs(MEMORY_DIR, exist_ok=True)

LINKS_FILE = os.path.join(MEMORY_DIR, "processed_links.txt")
CATEGORIES_FILE = os.path.join(MEMORY_DIR, "categories.txt")

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
    # FALLBACK SEGURO: Apenas esquemas estruturados
    images = []
    try:
        for schema in soup.find_all('script', type='application/ld+json'):
            try:
                data = json.loads(schema.string or "{}")
                items = data if isinstance(data, list) else [data]
                for item in items:
                    if item.get('@type') == 'Product' and item.get('image'):
                        img = item.get('image')
                        images.extend(img if isinstance(img, list) else [img])
            except: pass
    except: pass

    og = soup.find('meta', property='og:image')
    if og and og.get('content'):
        images.append(og['content'])

    return list(dict.fromkeys([i for i in images if isinstance(i, str) and 'logo' not in i.lower()]))

def get_smart_title(soup):
    h1 = soup.find('h1')
    if h1 and h1.text.strip(): return h1.text.strip()
    og = soup.find('meta', property='og:title')
    if og and og.get('content'): return og['content'].split(' - ')[0].strip()
    return soup.title.text.split(' - ')[0].strip() if soup.title else "Unnamed Product"

def extract_all_dimensions(text):
    m = re.findall(r'(\d+(?:\.\d+)?\s*(?:mm|cm|m)(?:\s*x\s*\d+(?:\.\d+)?\s*(?:mm|cm|m))?)', text, re.I)
    return " / ".join(dict.fromkeys([x.strip() for x in m])) if m else "Standard"

def get_smart_sizes_bs4(soup):
    sizes = []
    for sel in ['.swatch-option.text', '.size-selection', 'select[id*="attribute"] option', 'select[name*="size"] option', '.product-options-wrapper select option']:
        for el in soup.select(sel):
            t = el.get_text(strip=True)
            if t and not any(w in t.lower() for w in ["choose", "select", "selecione", "escolha"]):
                sizes.append(t)
        if sizes: break
    return list(dict.fromkeys(sizes))

def generate_optimized_content(title, desc, price, existing_categories, store_name, product_url, size_list=None):
    api_key = os.getenv("GOOGLE_API_KEY")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    size_from_title = extract_all_dimensions(title + " " + desc)
    
    try: price_float = float(str(price).replace(',', '.'))
    except: price_float = 0.0
    
    cats_str = ", ".join(f'"{c}"' for c in existing_categories)
    sizes_str = ", ".join(size_list) if size_list else "NO SIZES FOUND"
    fallback_inventory = [{"size": t, "qty": 1} for t in size_list] if size_list else [{"size": size_from_title, "qty": 1}]
    language_rule = "PORTUGUESE (Portugal). Output MUST be in Portuguese." if ".pt" in product_url or store_name in ["Leroy Merlin", "Obramat"] else "ENGLISH. Output MUST be in English."

    prompt = f"""
    You are an expert e-commerce catalog manager.
    Raw Title: {title}
    Raw Description: {desc}
    Language Rule: {language_rule}
    
    TASKS:
    1. Clean Title: Remove generic measurements, keep model name.
    2. Dynamic Category: Check if it fits in [{cats_str}]. If not, INVENT a new specific 1-2 word category.
    3. Color: Extract color/finish. Or "N/A".
    4. Sizes: Found sizes: [{sizes_str}]. Create inventory entry for EACH size. If NONE, use extracted size or "Standard".
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
        print(f"⚠️ AI Error: {e}")
    return fallback_data

def extract_with_real_browser(url, store_name):
    print(f"🤖 STEALTH BROWSER ACTIVE for {store_name}...")
    options = uc.ChromeOptions()
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--no-sandbox")

    driver = uc.Chrome(options=options, version_main=148)

    try:
        driver.get(url)
        print("⏳ Forcing Lazy-Load...")
        time.sleep(4)
        for _ in range(3):
            driver.execute_script("window.scrollBy(0, 500);")
            time.sleep(1.5)

        try: driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
        except: pass

        try:
            title = driver.find_element(By.CSS_SELECTOR, "h1.page-title span, h1, .product-title").get_attribute("textContent").strip()
        except:
            title = driver.title

        browser_price = None
        for _ in range(5):
            try:
                el = driver.find_element(By.CSS_SELECTOR, '.price-wrapper .price, span.price, .a-price .a-offscreen, [data-cerberus="ELEM_PRIX"]')
                m = re.search(r'(\d+[\.,]\d+)', (el.get_attribute("textContent") or el.text))
                if m:
                    browser_price = m.group(1).replace(',', '.')
                    break
            except: time.sleep(1)

        # --- SHIELD BLINDADO v3.0 (Anti-Janelas e Anti-Logotipos) ---
        photos = driver.execute_script("""
            const imgs = [...document.querySelectorAll('img')];
            const clean = [];

            for (const img of imgs) {
                const src = img.currentSrc || img.dataset.zoomImage || img.dataset.largeImage || img.dataset.src || img.src;
                if (!src || src.startsWith('data:')) continue;
                
                // Puxamos todo o texto possível da imagem para procurar lixo
                const altText = (img.alt || '').toLowerCase();
                const classText = (img.className || '').toLowerCase();
                const combinedText = src.toLowerCase() + ' ' + altText + ' ' + classText;

                // 1. O Filtro Supremo Anti-Lixo (Apaga Logos, Marcas, Selos de Anos e Garantias)
                if (/(logo|icon|sprite|payment|trust|banner|placeholder|brand|badge|selo|garantia|anos|years|marca)/i.test(combinedText)) continue;

                // 2. O Escudo Anti-Janela (Mata qualquer secção de relacionados)
                const inBad = img.closest('[class*="related"], [class*="recommend"], [class*="upsell"], [class*="cross"], [class*="bundle"], [class*="frequent"], [class*="frequentemente"], [class*="pack"]');
                if (inBad) continue;

                // 3. Procura nas galerias e em fotos normais da descrição
                const inGallery = img.closest('.product-gallery, .gallery, .swiper, .fotorama, .product-media, [class*="image-gallery"], [id*="gallery"], [class*="thumbnail"], [data-testid="main-image"], [class*="pdp"]');
                const w = img.naturalWidth || img.width;

                // Aceita se estiver na galeria ou for uma imagem isolada grande o suficiente
                if ((inGallery || w > 300) && w > 80) {
                    
                    // O TRUQUE DA OBRAMAT: Cortar a partir do '?' para ter a foto HD
                    let hdSrc = src.split('?')[0]; 
                    // Truque para remover redimensionamento (-150x150.jpg/.jpeg)
                    hdSrc = hdSrc.replace(/-\\d+x\\d+(?=\\.(jpg|jpeg|png|webp))/i, '');
                    
                    clean.push(hdSrc);
                }
            }
            return [...new Set(clean)];
        """)

        print(f"📸 Galeria principal bloqueada e capturada: {len(photos)} imagens válidas")

        html = driver.page_source
        return title, photos, html, None, [], browser_price
    finally:
        driver.quit()

def start_extraction(url):
    if os.path.exists(LINKS_FILE) and url in open(LINKS_FILE, encoding="utf-8").read():
        print("🛑 Link already extracted!")
        return

    store_name = "Store"
    if "woodies" in url: store_name = "Woodies"
    elif "amazon" in url: store_name = "Amazon"
    elif "diy" in url: store_name = "B&Q"
    elif "leroymerlin" in url: store_name = "Leroy Merlin"
    elif "prolinehardware" in url: store_name = "Proline Hardware"
    elif "obramat" in url: store_name = "Obramat"
    else:
        try: store_name = url.split('//')[1].split('/')[0].replace('www.','').split('.')[0].capitalize()
        except: pass

    print(f"🛒 {store_name} | Extraction Started...")

    raw_title, browser_photos, html_content, _, size_list, browser_price = extract_with_real_browser(url, store_name)
    soup = BeautifulSoup(html_content, 'html.parser')
    
    photo_list = list(dict.fromkeys(browser_photos + extract_all_images(soup)))
    
    if not size_list:
        size_list = get_smart_sizes_bs4(soup)

    if any(w in raw_title.lower() for w in ["404", "not found", "não encontrada", "pagina no encontrada"]):
        print("🛑 ALERT: Page not found (404)!"); return

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

    current_cats = load_categories()
    product_data = generate_optimized_content(raw_title, raw_desc, raw_price, current_cats, store_name, url, size_list)
    
    if product_data.get("category") not in current_cats: 
        save_category(product_data.get("category", "General"))

    path = os.path.join(DATA_DIR, "".join(c for c in product_data["name"] if c.isalnum() or c in " -_").strip()[:60])
    os.makedirs(path, exist_ok=True)

    with open(os.path.join(path, "data.json"), "w", encoding="utf-8") as f:
        json.dump(product_data, f, indent=4, ensure_ascii=False)

    dl = cloudscraper.create_scraper()
    count = 1
    for img_url in photo_list:
        if count > 5: break
        if img_url.startswith('//'): img_url = 'https:' + img_url
        elif img_url.startswith('/'): img_url = "https://" + url.split('/')[2] + img_url
        
        try:
            print(f"📥 Baixando Imagem Limpa: {img_url}")
            r = dl.get(img_url, timeout=15)
            if 'text/html' in r.headers.get('Content-Type','').lower(): continue
            
            tmp = os.path.join(path, f"photo_{count}.jpg")
            
            try:
                with Image.open(BytesIO(r.content)) as im:
                    if im.mode in ("RGBA", "P"):
                        im = im.convert("RGB")
                    
                    im.thumbnail((1200, 1200), Image.Resampling.LANCZOS)
                    im.save(tmp, "JPEG", quality=80, optimize=True)
            except Exception as e:
                continue
            
            if os.path.getsize(tmp) < 5120: 
                os.remove(tmp); continue
                
            print(f"✅ Photo {count} downloaded and compressed!")
            count += 1
        except Exception as e:
            pass

    with open(LINKS_FILE, "a", encoding="utf-8") as f: f.write(url + "\n")
    print(f"🚀 SUCCESS: {product_data['name']} | €{raw_price}")