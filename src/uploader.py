import os
import json
import requests
import glob
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

def get_secrets():
    try:
        import streamlit as st
        if "URL_PRODUTOS" in st.secrets and "ADMIN_API_SECRET" in st.secrets:
            return st.secrets["URL_PRODUTOS"], st.secrets["ADMIN_API_SECRET"]
    except ImportError:
        pass
    return os.getenv("URL_PRODUTOS"), os.getenv("ADMIN_API_SECRET")

def start_upload():
    api_url, api_key = get_secrets()
    
    if not api_url or not api_key:
        print("⚠️ ERRO: Chaves de API não encontradas!")
        return

    if not os.path.exists(DATA_DIR): return

    products = [p for p in os.listdir(DATA_DIR) if os.path.isdir(os.path.join(DATA_DIR, p))]

    for product in products:
        path = os.path.join(DATA_DIR, product)
        json_file = os.path.join(path, "data.json")
        if not os.path.exists(json_file): continue

        with open(json_file, "r", encoding="utf-8") as f:
            product_data = json.load(f)

        print(f"📤 Enviando para o Alvim: {product_data.get('name')}")

        # O Alvim espera 'payload' e não 'product_data'
        payload = {
            "payload": json.dumps(product_data) 
        }

        # Formato padrão de autorização que ele confirmou
        headers = {"Authorization": f"Bearer {api_key}"}

        image_paths = glob.glob(os.path.join(path, "*.jpg"))
        files = []
        for img_path in image_paths:
            # O Alvim espera o nome do campo como 'photos'
            files.append(('photos', (os.path.basename(img_path), open(img_path, 'rb'), 'image/jpeg')))

        try:
            # Envio como multipart/form-data
            res = requests.post(api_url, data=payload, files=files, headers=headers, timeout=60)

            if res.status_code in [200, 201]:
                print(f"✅ SUCESSO! Produto integrado no site.")
            else:
                print(f"⚠️ ERRO {res.status_code}: {res.text}")
                
        except Exception as e:
            print(f"❌ Erro de Conexão: {e}")
        finally:
            for _, file_tuple in files:
                file_tuple[1].close()

if __name__ == "__main__":
    start_upload()
