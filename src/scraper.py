import os
import json
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Carrega as chaves secretas do ficheiro .env
load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
HISTORY_FILE = os.path.join(BASE_DIR, "extracted_links_db.txt")

# Pega a chave do ficheiro secreto
api_key = os.getenv("GOOGLE_API_KEY")

def generate_optimized_content(original_title, original_description):
    """
    Usa o Gemini AI (via REST API super leve) para reescrever o titulo 
    e descricao para SEO unico e gramatica perfeita em Ingles.
    """
    if not api_key:
        print("⚠️ GOOGLE_API_KEY not found. Skipping AI rewrite.")
        return original_title, original_description

    print("🤖 AI is rewriting product content for SEO...")
    
    # URL direta da API do Google (nao precisa de bibliotecas pesadas)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    prompt = f"""
    You are an expert e-commerce copywriter and SEO specialist. 
    Take this original product name and description, and rewrite them 
    to be 100% unique, engaging, and grammatically perfect in English. 
    
    Guidelines:
    1. Create an optimized title that includes relevant keywords for search engines.
    2. Rewrite the description to highlight benefits, using bullet points for features.
    3. Ensure the tone is professional and appealing to buyers.
    4. Respond ONLY with a valid JSON object.
    
    Format example:
    {{
      "rewritten_title": "New Optimized Title Here",
      "rewritten_description": "New engaging description here..."
    }}
    
    Original Title: {original_title}
    Original Description: {original_description}
    """
    
    # Prepara o pacote de dados para enviar ao Google
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json"}
    }
    headers = {'Content-Type': 'application/json'}
    
    try:
        # Envia a mensagem para o cerebro da IA
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        # Desempacota a resposta
        data = response.json()
        
        # Verifica se o Google enviou o texto corretamente
        if 'candidates' in data and len(data['candidates']) > 0:
            ai_text = data['candidates'][0]['content']['parts'][0]['text']
            # Limpa formatacao extra do markdown caso o Google envie ```json
            ai_text = ai_text.strip().removeprefix('```json').removesuffix('```').strip()
            optimized_content = json.loads(ai_text)
            return optimized_content['rewritten_title'], optimized_content['rewritten_description']
        else:
            print("⚠️ Unexpected response from AI. Using original content.")
            return original_title, original_description
            
    except Exception as e:
        print(f"⚠️ AI Rewrite failed: {e}. Using original content.")
        return original_title, original_description

# --------------------------------------------------------

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
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-IE,en-GB,en;q=0.9,pt-PT;q=0.8',
        'Referer': '[https://www.diy.ie/](https://www.diy.ie/)',
        'DNT': '1'
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

        # A NOVA PARTE INTELIGENTE
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

        print("📸 Forcing original HD photos download...")
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

            src_lower = src.lower()
            if any(lixo in src_lower for lixo in black_list): continue

            src_clean = src.split('?')[0]

            if src_clean not in img_urls:
                img_urls.append(src_clean)

        img_count = 0
        for src in img_urls:
            try:
                img_data = requests.get(src, headers=headers, timeout=10).content
                if len(img_data) > 5000:
                    img_count += 1
                    img_name = f"image_{img_count}.jpg"
                    with open(os.path.join(product_path, img_name), 'wb') as handler:
                        handler.write(img_data)
            except Exception as e:
                print(f"  -> Image Error: {e}")

        save_extracted_link(url)
        print(f"✅ SUCCESS: Saved OPTIMIZED JSON and {img_count} HD images in folder {folder_name}")

    except Exception as e:
        print(f"❌ TECHNICAL ERROR: {e}")

if __name__ == "__main__":
    link = input("Link: ")
    start_extraction(link)
