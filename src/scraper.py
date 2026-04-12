import os, json, time, random, re
import cloudscraper
import requests
import shutil
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# --- NOVAS ARMAS PARA FURAR O CLOUDFLARE ---
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
# -------------------------------------------

load_dotenv()

# --- CAMINHOS BASE ---
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
                    if isinstance(img, list) and len(img) > 0: return img[0]
                    if isinstance(img, str): return img
    except: pass
    return None

def get_smart_title(soup):
    h1 = soup.find('h1')
    if h1 and h1.text.strip(): return h1.text.strip()
    og_title = soup.find('meta', property='og:title')
    if og_title and og_title.get('content'): 
        return og_title['content'].split(' - ')[0].strip()
    if soup.title and soup.title.text.strip():
        return soup.title.text.split(' - ')[0].strip()
    return "Produto Sem Nome"

def extract_all_dimensions(text):
    pattern = r'(\d+mm|\d+x\d+\s?cm)'
    matches = re.findall(pattern, text, re.IGNORECASE)
    return " x ".join(matches) if matches else "Standard"

# --- INTELIGÊNCIA ARTIFICIAL (CÉREBRO) ---
def generate_optimized_content(title, desc, price, existing_categories, store_name, product_url, lista_tamanhos=None):
    api_key = os.getenv("GOOGLE_API_KEY")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    size = extract_all_dimensions(title + " " + desc)
    
    try: price_float = float(price.replace(',', '.')) if price else 0.0
    except: price_float = 0.0

    cats_str = ", ".join(f'"{c}"' for c in existing_categories)
    tamanhos_str = ", ".join(lista_tamanhos) if lista_tamanhos else "Standard"

    prompt = f"""
    You are an expert e-commerce catalog manager.
    Raw Title: {title}
    Raw Description: {desc}
    
    TASKS:
    1. Clean Title: Remove generic measurements from the title to make it elegant, BUT keep essential model names. 
    2. Dynamic Category: STRICTLY categorize into ONE of these exact predefined categories: [{cats_str}]. 
       - RULE: If the product is a handle (door handle, maçaneta, puxador), you MUST choose "Handles".
       - RULE: If it is a hinge (dobradiça), you MUST choose "Hinges".
       - RULE: Only create a new 1-2 word category if it is absolutely impossible to fit into the list.
    3. Color: Extract the color, finish, or material (e.g., White, Chrome, Pine, Hardwood, Jet Black). If none, use "N/A".
    4. Identify Sizes: Clean and format ALL these sizes found on the page: [{tamanhos_str}]. 
       If the list is empty or just 'Standard', extract the size from the Title: {title}.
    5. Rewrite Description: Create a UNIQUE, professional plain text description. DO NOT use HTML tags.
    
    Return ONLY a valid JSON object matching EXACTLY this structure (no markdown blocks):
    {{
        "name": "<Cleaned Title>",
        "description": "<Your plain text description>",
        "category": "<Exact Category from list>",
        "color": "<Color or Finish>",
        "storeEntries": [
            {{
                "storeName": "{store_name}",
                "price": {price_float},
                "link": "{product_url}",
                "inventory": [
                    {{ "size": "<Size 1>", "qty": 1 }},
                    {{ "size": "<Size 2>", "qty": 1 }}
                ]
            }}
        ]
    }}
    """
    
    fallback_data = {
        "name": re.sub(r'(?i)(\(?[hwdt]\)?\s*)?\d+(?:mm|cm)x?|x\d+(?:mm|cm)', '', title).strip(' ,-'),
        "description": f"Premium quality {title}.\n\nIdeal for professional installations.",
        "category": "General",
        "color": "N/A",
        "storeEntries": [{"storeName": store_name, "price": price_float, "link": product_url, "inventory": [{"size": size, "qty": 1}]}]
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
        print(f"⚠️ Erro na IA, a usar fallback: {e}")
        return fallback_data
    return fallback_data

# --- O ROBÔ QUE ABRE O CHROME DE VERDADE ---
def extract_with_real_browser(url, store_name):
    print(f"🤖 Vestindo o Fato Mecânico para enganar a segurança da {store_name}...")
    options = uc.ChromeOptions()
    driver = uc.Chrome(options=options, version_main=146)
    
    try:
        driver.get(url)
        print("⏳ Esperando 8 segundos para a proteção nos deixar passar...")
        time.sleep(8) 
        
        driver.execute_script("window.scrollBy(0, 500);")
        time.sleep(2)
        
        try:
            title = driver.find_element(By.CSS_SELECTOR, "h1").text
        except:
            title = driver.title

        # --- NOVO: Captura de múltiplos tamanhos ---
        lista_tamanhos_brutos = []
        try:
            elementos_sizes = driver.find_elements(By.CSS_SELECTOR, '.swatch-option.text, .size-selection, [class*="size"] button')
            if not elementos_sizes and store_name == "TJ O'Mahony":
                elementos_sizes = driver.find_elements(By.CSS_SELECTOR, '.product-options-wrapper .size-grid-item')
            
            lista_tamanhos_brutos = [el.text.strip() for el in elementos_sizes if el.text.strip()]
        except:
            pass

        img_url = None
        foto_screenshot_path = None 
        
        try:
            if store_name == "Leroy Merlin":
                try:
                    meta_img = driver.find_element(By.CSS_SELECTOR, 'meta[property="og:image"]')
                    img_url = meta_img.get_attribute("content")
                except: pass
                
                if not img_url:
                    img_element = driver.find_element(By.CSS_SELECTOR, 'img[alt*="Porta"], picture img')
                    src = img_element.get_attribute("src")
                    if src and "data:image" not in src: 
                        img_url = src
            elif store_name == "TJ O'Mahony":
                try:
                    time.sleep(2)
                    fotorama_img = driver.find_element(By.CSS_SELECTOR, '.fotorama__loaded--img.fotorama__active img.fotorama__img')
                    img_url = fotorama_img.get_attribute("src")
                    print(f"🎯 Imagem TJ O'Mahony encontrada!")
                except: pass
            else:
                a_element = driver.find_element(By.CSS_SELECTOR, ".woocommerce-product-gallery__image a")
                img_url = a_element.get_attribute("href")
        except Exception as e:
            print("⚠️ Selenium não conseguiu a foto original.")
            
        if not img_url:
            print("📸 Imagem original protegida. O Robô vai tirar um Print Screen da tela!")
            caminho_temporario = os.path.join(BASE_DIR, "print_temporario.jpg")
            driver.save_screenshot(caminho_temporario)
            foto_screenshot_path = caminho_temporario 
            
        html = driver.page_source
        
        # Devolve 5 variáveis no total (incluindo a lista de tamanhos)
        return title, img_url, html, foto_screenshot_path, lista_tamanhos_brutos
        
    finally:
        print("🚪 Fechando o Chrome Automático...")
        driver.quit()
# ---------------------------------------------

def send_to_api(product_data, image_path):
    api_url = "https://lislock.pt/admin/api/admin/supplies"
    print("📡 A empacotar dados e enviar para a base de dados (API)...")
    try:
        payload_str = json.dumps(product_data)
        data = {'payload': payload_str}
        files = {}
        if image_path and os.path.exists(image_path):
            files = [('photos', ('foto_1.jpg', open(image_path, 'rb'), 'image/jpeg'))]
        response = requests.post(api_url, data=data, files=files if files else None, timeout=30)
        if response.status_code in [200, 201]:
            print("✅ SUCESSO: Item e Imagem inseridos no banco de dados!")
        else:
            print(f"⚠️ AVISO API: Servidor respondeu com status {response.status_code}.")
    except Exception as e:
        print(f"❌ ERRO API: Falha na comunicação: {e}")

def start_extraction(url):
    if os.path.exists(LINKS_FILE):
        with open(LINKS_FILE, "r", encoding="utf-8") as f:
            saved_links = [line.strip() for line in f.readlines()]
            if url in saved_links:
                print(f"\n🛑 AVISO: O link já foi extraído anteriormente!")
                return

    force_price_zero = False
    print(f"🕵️‍♂️ Analisando segurança do site...")
    
    # 1. Configuração do Roteador Automático
    sites_fato_mecanico = ["leroymerlin.pt", "tjomahony.ie", "prolinehardware.ie"]
    usar_selenium = any(site in url for site in sites_fato_mecanico)
    
    if "diy.ie" in url or "diy.com" in url: store_name = "B&Q"
    elif "screwfix.ie" in url: store_name = "Screwfix"
    elif "woodworkers.ie" in url: store_name = "WoodWorkers"
    elif "prolinehardware.ie" in url:
        store_name = "Proline Hardware"
        force_price_zero = True
    elif "leroymerlin.pt" in url: store_name = "Leroy Merlin"
    elif "tjomahony.ie" in url: store_name = "TJ O'Mahony"
    else: store_name = "Loja Padrão"

    print(f"🛒 Loja detetada: {store_name} | Fato Mecânico: {'SIM' if usar_selenium else 'NÃO'}")

    # 2. Execução da Extração
    print_automatico = None
    img_url_final = None
    lista_tamanhos_capturados = []

    if usar_selenium:
        try:
            # Recebendo perfeitamente as 5 variáveis do Fato Mecânico
            raw_title, img_url_browser, html_content, print_automatico, lista_tamanhos_capturados = extract_with_real_browser(url, store_name)
            soup = BeautifulSoup(html_content, 'html.parser')
            img_url_final = img_url_browser if img_url_browser else extract_main_image(soup)
        except Exception as e:
            print(f"❌ Erro no Fato Mecânico: {e}")
            return
    else:
        scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows'})
        try:
            time.sleep(random.uniform(2, 5))
            res = scraper.get(url, timeout=25)
            soup = BeautifulSoup(res.text, 'html.parser')
            raw_title = get_smart_title(soup)
            img_url_final = extract_main_image(soup)
        except Exception as e:
            print(f"❌ Erro na extração normal: {e}")
            return

    # 3. Processamento de Dados e IA
    try:
        print(f"🖨️ RADAR TÍTULO LIDO DA LOJA: '{raw_title}'") 

        if force_price_zero:
            raw_price = "0.00"
        else:
            raw_price = extract_price_from_schema(soup)
            if (not raw_price or raw_price == "75") and store_name == "Leroy Merlin":
                og_price = soup.find('meta', property='product:price:amount')
                if og_price and og_price.get('content'):
                    raw_price = og_price['content']
            
            if not raw_price or raw_price == "75" or raw_price == "0.00":
                 price_match = re.search(r'"price":\s?"(\d+[\.,]?\d*)"', str(soup))
                 raw_price = price_match.group(1) if price_match else "0.00"

        og_desc = soup.find('meta', property='og:description')
        if og_desc and og_desc.get('content'):
            raw_desc = og_desc['content']
        else:
            desc_tag = soup.find('div', {'id': 'product-details'}) or soup.find('div', class_='woocommerce-product-details__short-description')
            raw_desc = desc_tag.get_text() if hasattr(desc_tag, 'get_text') else raw_title

        current_cats = load_categories()
        
        # O Cérebro IA recebe a lista de tamanhos agora!
        product_data = generate_optimized_content(raw_title, raw_desc, raw_price, current_cats, store_name, url, lista_tamanhos_capturados)
        
        ai_cat = product_data.get("category", "General")
        if ai_cat not in current_cats: save_category(ai_cat)

        path = os.path.join(DATA_DIR, "".join(x for x in product_data["name"] if x.isalnum() or x in " -_").strip())
        os.makedirs(path, exist_ok=True)
        
        with open(os.path.join(path, "data.json"), "w", encoding="utf-8") as f:
            json.dump(product_data, f, indent=4, ensure_ascii=False)

        # 4. Gestão da Imagem
        foto_final_path = None
        
        if print_automatico and os.path.exists(print_automatico):
            foto_final_path = os.path.join(path, "foto_1.jpg")
            shutil.move(print_automatico, foto_final_path)
            print("✅ Print automático anexado e movido com sucesso!")
            
        elif img_url_final:
            if img_url_final.startswith('//'): img_url_final = 'https:' + img_url_final
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            try:
                img_data = requests.get(img_url_final, headers=headers, timeout=15).content
                foto_final_path = os.path.join(path, "foto_1.jpg")
                with open(foto_final_path, 'wb') as handler:
                    handler.write(img_data)
                print("✅ Fotografia oficial guardada com sucesso!")
            except Exception as e:
                print(f"⚠️ Erro ao tentar baixar a foto oficial: {e}")
        else:
            print("⚠️ Nenhuma foto oficial encontrada e nenhum print tirado.")

        # 5. Finalização
        print(f"🚀 SUCESSO LOCAL: {product_data['name']} | €{raw_price}")
        send_to_api(product_data, foto_final_path)
        
        with open(LINKS_FILE, "a", encoding="utf-8") as f: f.write(url + "\n")

    except Exception as e: 
        print(f"❌ FALHA FINAL: {e}")