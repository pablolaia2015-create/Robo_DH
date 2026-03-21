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
    if not api_url or not api_key: return

    products = [p for p in os.listdir(DATA_DIR) if os.path.isdir(os.path.join(DATA_DIR, p))]

    for product in products:
        path = os.path.join(DATA_DIR, product)
        json_file = os.path.join(path, "data.json")
        if not os.path.exists(json_file): continue

        with open(json_file, "r", encoding="utf-8") as f:
            product_data = json.load(f)

        # O Alvim usa formData.get("payload") no código dele
        payload = {"payload": json.dumps(product_data)}

        # TÉCNICA CHAVE-MESTRA: Envia a senha em 3 formatos comuns
        headers = {
            "Authorization": f"Bearer {api_key}",
            "x-api-key": api_key,
            "admin-api-secret": api_key
        }

        image_paths = glob.glob(os.path.join(path, "*.jpg"))
        files = []
        for img_path in image_paths:
            # O Alvim usa formData.getAll("photos")
            files.append(('photos', (os.path.basename(img_path), open(img_path, 'rb'), 'image/jpeg')))

        try:
            print(f"📤 Tentando upload para: {api_url}")
            res = requests.post(api_url, data=payload, files=files, headers=headers, timeout=60)

            if res.status_code in [200, 201]:
                print(f"✅ SUCESSO ABSOLUTO!")
            else:
                print(f"⚠️ FALHA {res.status_code}: {res.text}")
        except Exception as e:
            print(f"❌ Erro: {e}")
        finally:
            for _, f_tuple in files: f_tuple[1].close()

if __name__ == "__main__":
    start_upload()
