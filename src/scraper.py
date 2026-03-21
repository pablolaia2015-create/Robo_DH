import os
import json
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
HISTORY_FILE = os.path.join(BASE_DIR, "extracted_links_db.txt")

def get_api_key():
    try:
        import streamlit as st
        if "GOOGLE_API_KEY" in st.secrets:
            return st.secrets["GOOGLE_API_KEY"]
    except ImportError:
        pass
    return os.getenv("GOOGLE_API_KEY")

def generate_optimized_content(original_title, original_description, original_price):
    api_key = get_api_key()
    
    # Plano B de emergência caso a IA falhe (Formato Exato do Alvim)
    fallback_data = {
        "name": original_title,
        "description": f"<p>{original_description}</p>",
        "category": "Uncategorized",
        "serviceSlug": "uncategorized",
        "color": "Standard",
        "storeEntries": [{
            "storeName": "B&Q",
            "price": float(original_price) if original_price else 0.0,
            "inventory": [{"size": "Standard", "qty": 1}]
        }]
    }
    
    if not api_key:
        print("⚠️ ERRO CRÍTICO: Chave GOOGLE_API_KEY não foi encontrada!")
        return fallback_data

    print("🤖 AI is rewriting and structuring data for Alvim's database...")
    
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key={api_key}"
    
    prompt = f"""
    You are an expert e-commerce data extractor and copywriter for a DIY store.
    Read this raw product title, description, and price:
    Title: {original_title}
    Description: {original_description}
    Price: {original_price}
    
    Create an optimized product listing following these EXACT rules:
    1. 'name': SEO-optimized, clean product name.
    2. 'description': Engaging description highlighting benefits. IMPORTANT: Format using ONLY standard HTML tags (<p>, <b>, <ul>, <li>, <br>). DO NOT use Markdown asterisks (**).
    3. 'category': MUST be exactly one of these: "Internal Doors", "Front Doors", "Bathroom Doors", "Handles", "Hinges", "Locks", "Cleaning Supplies", "Painting Supplies". Pick the most logical one.
    4. 'serviceSlug': URL-friendly version of the category (e.g., "internal-doors", "handles").
    5. 'color': Extract or infer the main color/finish (e.g., "Natural Pine", "Chrome"). If unknown, use "Standard".
    6. 'storeEntries': An array with one object containing:
       - 'storeName': "B&Q"
       - 'price': The numerical price as a float (e.g., 145.00)
       - 'inventory': An array with one object containing 'size' (extract physical dimensions like "(h)1981mm (w)762mm") and 'qty' (always 1).

    Respond ONLY with a valid JSON object matching this exact structure:
    {{
      "name": "...",
      "description": "...",
      "category": "...",
      "serviceSlug": "...",
      "color": "...",
      "storeEntries": [
        {{
          "storeName": "B&Q",
          "price": 0.00,
          "inventory": [
            {{
              "size": "...",
              "qty": 1
            }}
          ]
        }}
      ]
    }}
    """
    
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    headers = {'Content-Type': 'application/json'}
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code != 200:
            print(f"⚠️ FALHA NA IA: {response.text}")
            return fallback_data
            
        data = response.json()
        if 'candidates' in data and len(data['candidates']) > 0:
            ai_text = data['candidates'][0]['content']['parts'][0]['text']
            ai_text = ai_text.strip().removeprefix('```json').removesuffix('```').strip()
            optimized_content = json.loads(ai_text)
            print("✅ IA gerou o JSON no formato do Alvim perfeitamente!")
            return optimized_content
        else:
            return fallback_data
            
    except Exception as e:
        print(f"⚠️ ERRO NA IA: {str(e)}")
        return fallback_data

def is_link_extracted(url):
    if not os.path.exists(HISTORY_FILE):
        return False
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        links = f.read().splitlines()
    return url in links

def save_extracted_link(url):
    with open(HISTORY_FILE, "a", encoding="utf-8") as f:
        f.write(url + "\n")

def start_extraction(url):
    print(f"\n🔍 SCRAPING TARGET: {url}")
    if is_link_extracted(url):
        print("⚠️ WARNING: This link was already extracted. Skipping...")
        return

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-IE,en-GB,en;q=0.9',
        'Referer': 'https://www.diy.ie/',
    }

    try:
        res = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')

        h1_tag = soup.find('h1')
        title_text = h1_tag.text.strip() if h1_tag else "Unknown Product"

        if "techies" in title_text.lower() or "blocked" in title_text.lower():
            print("❌ ACCESS DENIED: The website blocked the robot.")
            return

        price_tag = soup.find('div', {'data-test-id': 'product-price'})
        raw_price = price_tag.text.replace('€', '').strip() if price_tag else "0.00"

        desc_tag = soup.find('div', {'id': 'product-details'})
        description = desc_tag.text.strip()[:600] if desc_tag else "No description available."

        # MAGIA DA IA ACONTECE AQUI (Enviamos também o preço cru para ela tratar)
        product_data = generate_optimized_content(title_text, description, raw_price)
        
        # O Robô injeta a URL no JSON gerado pela IA
        try:
            product_data["storeEntries"][0]["link"] = url
        except KeyError:
            pass

        folder_name = "".join(x for x in product_data.get("name", title_text) if x.isalnum() or x in " -_").strip()
        product_path = os.path.join(DATA_DIR, folder_name)
        os.makedirs(product_path, exist_ok=True)

        with open(os.path.join(product_path, "data.json"), "w", encoding="utf-8") as f:
            json.dump(product_data, f, indent=4, ensure_ascii=False)

        print("📸 Downloading images...")
        img_urls = []
        og_image = soup.find('meta', property='og:image')
        if og_image and og_image.get('content'):
            img_urls.append(og_image['content'].split('?')[0])

        black_list = ['thumb', 'icon', 'logo', 'badge', 'svg', 'avatar']
        for img in soup.find_all('img'):
            src = img.get('src') or img.get('data-src')
            if not src: continue
            if src.startswith('//'): src = 'https:' + src
            if not src.startswith('http'): continue
            if any(lixo in src.lower() for lixo in black_list): continue
            
            src_clean = src.split('?')[0]
            if src_clean not in img_urls:
                img_urls.append(src_clean)

        img_count = 0
        for src in img_urls:
            try:
                img_data = requests.get(src, headers=headers, timeout=10).content
                if len(img_data) > 5000:
                    img_count += 1
                    with open(os.path.join(product_path, f"image_{img_count}.jpg"), 'wb') as handler:
                        handler.write(img_data)
            except:
                pass

        save_extracted_link(url)
        print(f"✅ SAVED in folder {folder_name}")

    except Exception as e:
        print(f"❌ EXTRACTION ERROR: {e}")
