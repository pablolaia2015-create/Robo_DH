import os
import json
import requests
from bs4 import BeautifulSoup

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

def start_extraction(url):
    print(f"\n🔍 SCRAPING TARGET: {url}")

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-IE,en-GB,en;q=0.9,pt-PT;q=0.8',
        'Referer': 'https://www.diy.ie/',
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

        name = title_text
        price_tag = soup.find('div', {'data-test-id': 'product-price'})
        price = price_tag.text.replace('€', '').strip() if price_tag else "0.00"

        desc_tag = soup.find('div', {'id': 'product-details'})
        description = desc_tag.text.strip()[:600] if desc_tag else "No description available."

        product_data = {
            "name": name,
            "category": "Hardware",
            "finish": "Standard",
            "description": description,
            "store": "B&Q",
            "price": price,
            "url": url,
            "size": "N/A",
            "quantity": 1
        }

        folder_name = "".join(x for x in name if x.isalnum() or x in " -_").strip()
        product_path = os.path.join(DATA_DIR, folder_name)
        os.makedirs(product_path, exist_ok=True)

        with open(os.path.join(product_path, "data.json"), "w", encoding="utf-8") as f:
            json.dump(product_data, f, indent=4, ensure_ascii=False)

        # --- 📸 MÁQUINA FOTOGRÁFICA (FORÇAR ALTA RESOLUÇÃO) ---
        print("📸 A forçar o download das fotos originais (HD)...")
        img_urls = []
        
        og_image = soup.find('meta', property='og:image')
        if og_image and og_image.get('content'):
            img_urls.append(og_image['content'].split('?')[0]) # O segredo do corte!
            
        black_list = ['thumb', 'icon', 'logo', 'badge', 'svg', 'avatar']

        for img in soup.find_all('img'):
            src = img.get('src') or img.get('data-src')
            if not src: continue
            if src.startswith('//'): src = 'https:' + src
            if not src.startswith('http'): continue
                
            src_lower = src.lower()
            if any(lixo in src_lower for lixo in black_list): continue
                
            # O GRANDE TRUQUE: Cortar tudo o que está depois do "?" no link!
            # Isto destrói a ordem de encolher a foto e traz o tamanho gigante real.
            src_clean = src.split('?')[0]
            
            if src_clean not in img_urls:
                img_urls.append(src_clean)

        img_count = 0
        for src in img_urls:
            try:
                img_data = requests.get(src, headers=headers, timeout=10).content
                # Filtra fotos que são demasiado pequenas em peso (menos de 5KB = lixo)
                if len(img_data) > 5000:
                    img_count += 1
                    img_name = f"imagem_{img_count}.jpg"
                    with open(os.path.join(product_path, img_name), 'wb') as handler:
                        handler.write(img_data)
            except Exception as e:
                print(f"  -> Erro na imagem: {e}")

        print(f"✅ SUCCESS: Guardado o JSON e {img_count} imagens HD na pasta {folder_name}")

    except Exception as e:
        print(f"❌ TECHNICAL ERROR: {e}")

if __name__ == "__main__":
    link = input("Link: ")
    start_extraction(link)

