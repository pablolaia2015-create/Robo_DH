import os
import json
import requests
from bs4 import BeautifulSoup

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

def start_extraction(url):
    print(f"\n🔍 SCRAPING TARGET: {url}")
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')

        # --- MAPEAMENTO BASEADO NA IMAGEM ---
        name = soup.find('h1').text.strip() if soup.find('h1') else "Unknown"
        
        # Tenta pegar preço (ajustar se o site mudar)
        price_tag = soup.find('span', {'data-test-id': 'product-price'})
        price = price_tag.text.replace('€', '').strip() if price_tag else "0.00"

        # Tenta pegar descrição
        desc_tag = soup.find('div', {'id': 'product-details'})
        description = desc_tag.text.strip()[:500] if desc_tag else "No description."

        # Monta o JSON exatamente como o formulário "New Supply" pede
        product_data = {
            "name": name,
            "category": "Hardware", # Padrão
            "finish": "Standard",   # Pode ser refinado depois
            "description": description,
            "store": "B&Q",         # Padrão
            "price": price,
            "url": url,
            "size": "N/A",          # Pode ser refinado depois
            "quantity": 1           # Padrão
        }

        # Criar pasta e salvar
        folder_name = "".join(x for x in name if x.isalnum() or x in " -_").strip()
        path = os.path.join(DATA_DIR, folder_name)
        if not os.path.exists(path): os.makedirs(path)

        with open(os.path.join(path, "data.json"), "w", encoding="utf-8") as f:
            json.dump(product_data, f, indent=4)
            
        print(f"✅ Data mapped and saved: {folder_name}")

    except Exception as e:
        print(f"❌ Scraper Error: {e}")
