import os
import json
import requests
from bs4 import BeautifulSoup

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

def start_extraction(url):
    print(f"\n🔍 SCRAPING: {url}")
    
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Lógica para pegar o nome (exemplo genérico, o Alvim ajustará depois)
        title = soup.title.string.split('|')[0].strip() if soup.title else "New Product"
        
        # Criar a pasta do produto dentro de 'data'
        folder_name = "".join(x for x in title if x.isalnum() or x in " -_").strip()
        product_path = os.path.join(DATA_DIR, folder_name)
        
        if not os.path.exists(product_path):
            os.makedirs(product_path)

        # Criar o arquivo data.json
        product_data = {
            "name": title,
            "url": url,
            "category": "Hardware",
            "store": "B&Q"
        }

        with open(os.path.join(product_path, "data.json"), "w", encoding="utf-8") as f:
            json.dump(product_data, f, indent=4)
            
        print(f"✅ Product folder created: data/{folder_name}")
        print(f"✅ data.json saved successfully.")

    except Exception as e:
        print(f"❌ Scraping Failed: {e}")

