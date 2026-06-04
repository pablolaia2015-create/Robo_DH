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

# --- EXTRATORES AUXILIARES ---
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
    # Procura padrões como "1200mm", "1200 mm", "1.2m", "120x60cm", "120 x 60 cm"
    pattern = r'(\d+(?:\.\d+)?\s*(?:mm|cm|m)(?:\s*x\s*\d+(?:\.\d+)?\s*(?:mm|cm|m))?)'
    matches = re.findall(pattern, text, re.IGNORECASE)
    # Remove duplicados mantendo a ordem e junta tudo
    return " / ".join(list(dict.fromkeys([m.strip() for m in matches]))) if matches else "Standard"

# NOVO: Radar de Tamanhos para Extração Rápida (Cloudscraper)
def get_smart_sizes_bs4(soup):
    tamanhos = []
    try:
        seletores = [
            '.swatch-option.text', 
            '.size-selection', 
            'select[id*="attribute"] option', 
            'select[name*="size"] option',
            '.product-options-wrapper select option'
        ]
        for seletor in seletores:
            elementos = soup.select(seletor)
            for el in elementos:
                texto = el.get_text(strip=True)
                if texto and not any(palavra in texto.lower() for palavra in ["choose", "select", "selecione", "escolha"]):
                    tamanhos.append(texto)
            if tamanhos: break # Se achou tamanhos com um seletor, para de procurar
    except: pass
    return list(dict.fromkeys(tamanhos))

# --- INTELIGÊNCIA ARTIFICIAL (CÉREBRO) ---
def generate_optimized_content(title, desc, price, existing_categories, store_name, product_url, lista_tamanhos=None):
    api_key = os.getenv("GOOGLE_API_KEY")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    size_from_title = extract_all_dimensions(title + " " + desc)
    
    try: price_float = float(price.replace(',', '.')) if price else 0.0
    except: price_float = 0.0

    cats_str = ", ".join(f'"{c}"' for c in existing_categories)
    tamanhos_str = ", ".join(lista_tamanhos) if lista_tamanhos else "NO SIZES FOUND"

    if lista_tamanhos:
        fallback_inventory = [{"size": t, "qty": 1} for t in lista_tamanhos]
    else:
        fallback_inventory = [{"size": size_from_title, "qty": 1}]

    # 🌍 Roteador de Idiomas
    if ".pt" in product_url or store_name == "Leroy Merlin":
        idioma = "PORTUGUESE (Portugal). The output MUST be entirely in Portuguese (Categories, colors, descriptions)."
    else:
        idioma = "ENGLISH. The output MUST be entirely in English."

    prompt = f"""
    You are an expert e-commerce catalog manager.
    Raw Title: {title}
    Raw Description: {desc}
    
    CRITICAL RULE: All generated text (name, description, category, color) MUST BE in {idioma}.
    
    TASKS:
    1. Clean Title: Remove generic measurements from the title to make it elegant, BUT keep essential model names. 
    2. Dynamic Category: STRICTLY categorize into ONE of these exact predefined categories: [{cats_str}]. 
       - RULE: If the product is a handle (door handle, maçaneta, puxador), you MUST choose "Handles".
       - RULE: If it is a hinge (dobradiça), you MUST choose "Hinges".
       - RULE: Only create a new 1-2 word category if it is absolutely impossible to fit into the list.
    3. Color: Extract the color, finish, or material (e.g., White, Chrome, Pine, Hardwood, Jet Black). If none, use "N/A".
    4. Identify Sizes: The scraper found these sizes on the page: [{tamanhos_str}]. 
       - IF the list says "NO SIZES FOUND", try to extract the size from the Title: {title}. If none, use "Standard".
       - CRITICAL: IF sizes ARE provided in the list (e.g. 50mm, 60mm), you MUST create an inventory entry for EACH size in the JSON. Do not output 'Standard' if specific sizes were found!
    5. Rewrite Description: Create a UNIQUE, professional plain text description. DO NOT use HTML tags.
    
    Return ONLY a valid JSON object matching EXACTLY this structure (no markdown blocks):
    {{
        "name": "<Cleaned Title>",
        "description": "<Your plain text description>",
        "category": "<Exact Category from list or translated equivalent>",
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
        print(f"⚠️ Erro na IA, a usar fallback: {e}")
        return fallback_data
    return fallback_data

# --- O ROBÔ QUE ABRE O CHROME DE VERDADE ---
def extract_with_real_browser(url, store_name):
    print(f"🤖 Vestindo o Fato Mecânico para enganar a segurança da {store_name}...")
    options = uc.ChromeOptions()
    options.add_argument("--window-size=1920,1080") 
    driver = uc.Chrome(options=options, version_main=148)
    
    try:
        driver.get(url)
        print("⏳ Esperando 8 segundos para a proteção e os preços carregarem...")
        time.sleep(15) 
        
        try:
            botoes_cookies = driver.find_elements(By.XPATH, "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'aceitar')] | //button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'accept')]")
            if botoes_cookies:
                botoes_cookies[0].click()
                time.sleep(2)
        except: pass
        
        driver.execute_script("window.scrollBy(0, 500);")
        time.sleep(2)
        
        try:
            title = driver.find_element(By.CSS_SELECTOR, "h1").text
        except:
            title = driver.title

        # 📏 NOVO: Radar Universal de Tamanhos (Apanha Dropdowns e Swatches)
        lista_tamanhos_brutos = []
        try:
            seletores_tamanhos = [
                '.swatch-option.text', 
                '.size-selection', 
                '[class*="size"] button',
                '.product-options-wrapper select[id*="attribute"] option', # Magento Dropdown (TJ O'Mahony)
                'select[name*="size"] option',
                'select[name*="attribute"] option',
                '.radio-button-labels label'
            ]
            
            for seletor in seletores_tamanhos:
                elementos = driver.find_elements(By.CSS_SELECTOR, seletor)
                for el in elementos:
                    texto = el.get_attribute("textContent")
                    if not texto: texto = el.text
                    texto = texto.strip()
                    # Bloqueia palavras genéricas
                    if texto and not any(palavra in texto.lower() for palavra in ["choose", "select", "selecione", "escolha", "option"]):
                        lista_tamanhos_brutos.append(texto)
                
                if lista_tamanhos_brutos:
                    # Remove duplicados
                    lista_tamanhos_brutos = list(dict.fromkeys(lista_tamanhos_brutos))
                    print(f"📏 Tamanhos detetados pelo Fato Mecânico: {lista_tamanhos_brutos}")
                    break
        except: pass

        # 💰 CAPTURA DO PREÇO A QUENTE 
        browser_price = None
        if store_name == "Leroy Merlin":
            print("💶 À procura do preço na página (Aguardando renderização)...")
            for tentativa in range(15):
                try:
                    price_elem = driver.find_element(By.CSS_SELECTOR, '[data-cerberus="ELEM_PRIX"], .kl-hidden-accessibility, .m-price__line')
                    texto_preco = price_elem.get_attribute("textContent") or price_elem.text
                    match = re.search(r'(\d+[\.,]\d+)', texto_preco)
                    if match:
                        browser_price = match.group(1).replace(',', '.')
                        print(f"✅ Preço LM apanhado com sucesso: {browser_price} €")
                        break 
                except: pass
                time.sleep(1)
                
        elif store_name == "Amazon":
            print("💶 À procura do preço na Amazon...")
            for tentativa in range(10):
                try:
                    # A Amazon usa várias classes diferentes para o preço
                    price_elem = driver.find_element(By.CSS_SELECTOR, '.a-price .a-offscreen, #priceblock_ourprice, .a-color-price')
                    texto_preco = price_elem.get_attribute("textContent") or price_elem.text
                    match = re.search(r'(\d+[\.,]\d+)', texto_preco)
                    if match:
                        browser_price = match.group(1).replace(',', '.')
                        print(f"✅ Preço Amazon apanhado com sucesso: {browser_price} €")
                        break 
                except: pass
                time.sleep(1)
            
        if not browser_price:
            print("⚠️ O preço não apareceu no ecrã a tempo, vamos tentar no código-fonte...")

        img_url = None
        foto_screenshot_path = None
        
        try:
            if store_name == "Leroy Merlin":
                try:
                    meta_img = driver.find_element(By.CSS_SELECTOR, 'meta[property="og:image"]')
                    img_url = meta_img.get_attribute("content")
                except: pass
                if not img_url:
                    img_element = driver.find_element(By.CSS_SELECTOR, 'picture img, [data-testid="main-image"]')
                    src = img_element.get_attribute("src")
                    if src and "data:image" not in src: img_url = src
            elif store_name == "TJ O'Mahony":
                try:
                    time.sleep(2)
                    fotorama_img = driver.find_element(By.CSS_SELECTOR, '.fotorama__loaded--img.fotorama__active img.fotorama__img')
                    img_url = fotorama_img.get_attribute("src")
                except: pass
            elif store_name == "Woodies":
                try:
                    meta_img = driver.find_element(By.CSS_SELECTOR, 'meta[property="og:image"]')
                    img_url = meta_img.get_attribute("content")
                except: pass
            elif store_name == "Amazon":
                try:
                    # A imagem principal da Amazon fica no landingImage ou imgBlkFront
                    img_element = driver.find_element(By.CSS_SELECTOR, '#landingImage, #imgBlkFront')
                    img_url = img_element.get_attribute("src")
                    # Tenta ir buscar a versão de Alta Resolução se existir
                    high_res = img_element.get_attribute("data-old-hires")
                    if high_res and "http" in high_res: img_url = high_res
                except: pass
            else:
                a_element = driver.find_element(By.CSS_SELECTOR, ".woocommerce-product-gallery__image a")
                img_url = a_element.get_attribute("href")
        except Exception as e:
            print("⚠️ Selenium não conseguiu a foto original.")
            
        if not img_url:
            print("📸 Tirando um Print Screen limpo da tela...")
            caminho_temporario = os.path.join(BASE_DIR, "print_temporario.jpg")
            driver.save_screenshot(caminho_temporario)
            foto_screenshot_path = caminho_temporario 
            
        html = driver.page_source
        return title, img_url, html, foto_screenshot_path, lista_tamanhos_brutos, browser_price
        
    finally:
        print("🚪 Fechando o Chrome Automático...")
        driver.quit()

# --- FUNÇÃO PRINCIPAL DE ARRANQUE ---
def start_extraction(url):
    # 1. Verificação de Duplicados
    if os.path.exists(LINKS_FILE):
        with open(LINKS_FILE, "r", encoding="utf-8") as f:
            saved_links = [line.strip() for line in f.readlines()]
            if url in saved_links:
                print(f"\n🛑 AVISO: O link já foi extraído anteriormente!")
                return

    force_price_zero = False
    print(f"🕵️‍♂️ Analisando segurança do site...")
    
    # 2. Definição do Fato Mecânico
    sites_fato_mecanico = ["leroymerlin.pt", "tjomahony.ie", "prolinehardware.ie", "woodies.ie", "amazon."]
    usar_selenium = any(site in url.lower() for site in sites_fato_mecanico)
    
    # 3. Identificação Inteligente da Loja
    if "diy.ie" in url or "diy.com" in url: store_name = "B&Q"
    elif "screwfix.ie" in url: store_name = "Screwfix"
    elif "woodworkers.ie" in url: store_name = "WoodWorkers"
    elif "prolinehardware.ie" in url:
        store_name = "Proline Hardware"
        force_price_zero = True
    elif "leroymerlin.pt" in url: store_name = "Leroy Merlin"
    elif "tjomahony.ie" in url: store_name = "TJ O'Mahony"
    elif "woodies.ie" in url: store_name = "Woodies"
    elif "amazon." in url.lower(): store_name = "Amazon"  # <-- ATUALIZADO PARA AMAZON
    else:
        # CÉREBRO DINÂMICO
        try:
            from urllib.parse import urlparse
            dominio = urlparse(url).netloc
            nome_base = dominio.replace('www.', '').split('.')[0]
            store_name = nome_base.capitalize()
        except:
            store_name = "Loja Padrão"

    print(f"🛒 Loja detetada: {store_name} | Fato Mecânico: {'SIM' if usar_selenium else 'NÃO'}")

    print_automatico = None
    img_url_final = None
    lista_tamanhos_capturados = []
    browser_price = None

    if usar_selenium:
        try:
            raw_title, img_url_browser, html_content, print_automatico, lista_tamanhos_capturados, browser_price = extract_with_real_browser(url, store_name)
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
            # 📏 Radar de tamanhos também para extração normal!
            lista_tamanhos_capturados = get_smart_sizes_bs4(soup)
            if lista_tamanhos_capturados:
                print(f"📏 Tamanhos detetados (Normal): {lista_tamanhos_capturados}")
        except Exception as e:
            print(f"❌ Erro na extração normal: {e}")
            return

    try:
        print(f"🖨️ RADAR TÍTULO LIDO DA LOJA: '{raw_title}'") 

        # 🛡️ ESCUDO ANTI-LIXO 
        titulos_proibidos = ["substituída", "não encontrada", "404", "indisponível", "not found", "page not found"]
        if any(palavra in raw_title.lower() for palavra in titulos_proibidos):
            print("🛑 ALERTA: A página não existe ou o link está quebrado!")
            return 

        # 💰 LÓGICA DE PREÇOS
        if force_price_zero:
            raw_price = "0.00"
        elif browser_price:
            raw_price = browser_price
        else:
            raw_price = extract_price_from_schema(soup)
            
            if (not raw_price or raw_price in ["75", "0.00", "0", None]) and store_name == "Leroy Merlin":
                og_price = soup.find('meta', property='product:price:amount')
                if og_price and og_price.get('content'): raw_price = og_price['content']
                
                if not raw_price or raw_price in ["75", "0.00", "0", None]:
                    hidden_price = soup.find('span', class_='kl-hidden-accessibility')
                    if hidden_price:
                        match = re.search(r'(\d+[\.,]\d+)', hidden_price.text)
                        if match: raw_price = match.group(1).replace(',', '.')

            if not raw_price or raw_price in ["75", "0.00", "0", None]:
                 price_match = re.search(r'"price":\s?"?(\d+[\.,]?\d*)"?', str(soup))
                 if price_match: raw_price = price_match.group(1).replace(',', '.')
                 else: raw_price = "0.00"

        og_desc = soup.find('meta', property='og:description')
        if og_desc and og_desc.get('content'):
            raw_desc = og_desc['content'].strip()
        else:
            desc_tag = soup.find('div', {'id': 'product-details'}) or soup.find('div', class_='woocommerce-product-details__short-description')
            raw_desc = desc_tag.get_text(strip=True) if desc_tag else raw_title

        current_cats = load_categories()
        
        product_data = generate_optimized_content(raw_title, raw_desc, raw_price, current_cats, store_name, url, lista_tamanhos_capturados)
        
        ai_cat = product_data.get("category", "General")
        if ai_cat not in current_cats: save_category(ai_cat)

        path = os.path.join(DATA_DIR, "".join(x for x in product_data["name"] if x.isalnum() or x in " -_").strip())
        os.makedirs(path, exist_ok=True)
        
        with open(os.path.join(path, "data.json"), "w", encoding="utf-8") as f:
            json.dump(product_data, f, indent=4, ensure_ascii=False)

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

        print(f"🚀 SUCESSO LOCAL: {product_data['name']} | €{raw_price}")
        
        with open(LINKS_FILE, "a", encoding="utf-8") as f: f.write(url + "\n")

    except Exception as e: 
        print(f"❌ FALHA FINAL: {e}")