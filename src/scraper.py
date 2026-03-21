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

def generate_optimized_content(original_title, original_description):
    api_key = get_api_key()
    
    if not api_key:
        print("⚠️ ERRO CRÍTICO: Chave GOOGLE_API_KEY não foi encontrada pelo scraper!")
        return original_title, original_description

    print("🤖 AI is rewriting product content for SEO...")
    
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    prompt = f"""
    You are an expert e-commerce copywriter and SEO specialist. 
    Take this original product name and description, and rewrite them 
    to be 100% unique, engaging, and grammatically perfect in English. 
    
    Guidelines:
    1. Create an optimized title that includes relevant keywords for search engines.
    2. Rewrite the description to highlight benefits, using bullet points for features. 
       CRITICAL: If the Original Description says 'No description available.', invent a highly professional description based solely on the title.
    3. Respond ONLY with a valid JSON object.
    
    Format example:
    {{
      "rewritten_title": "New Optimized Title Here",
      "rewritten_description": "New engaging description here..."
    }}
    
    Original Title: {original_title}
    Original Description: {original_description}
    """
    
    # PACOTE LIMPO: Removida a configuração que a v1 não aceitava
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    headers = {'Content-Type': 'application/json'}
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code != 200:
            print(f"⚠️ FALHA NA IA (Erro {response.status_code}): {response.text}")
            return original_title, original_description
            
        data = response.json()
        if 'candidates' in data and len(data['candidates']) > 0:
            ai_text = data['candidates'][0]['content']['parts'][0]['text']
            ai_text = ai_text.strip().removeprefix('```json').removesuffix('```').strip()
            optimized_content = json.loads(ai_text)
            print("✅ IA reescreveu os textos com sucesso!")
            return optimized_content['rewritten_title'], optimized_content['rewritten_description']
        else:
            print("⚠️ A IA não devolveu candidatos válidos.")
            return original_title, original_description
            
    except Exception as e:
        print(f"⚠️ ERRO DE CÓDIGO NA IA: {str(e)}")
        return original_title, original_description

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
        price = price_tag.text.replace('€', '').strip() if price_tag else "0.00"

        desc_tag = soup.find('div', {'id': 'product-details'})
        description = desc_tag.text.strip()[:600] if desc_tag else "No description available."

        rewritten_title, rewritten_description = generate_optimized_content(title_text, description)

        product_data = {
            "name": rewritten_title,
            "category": "Hardware",
            "finish": "Standard",
            "description": rewritten_description,
            "store": "B&Q",
            "price": price,
            "url": url,
            "size": "N/A",
            "quantity": 1
        }

        folder_name = "".join(x for x in rewritten_title if x.isalnum() or x in " -_").strip()
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
