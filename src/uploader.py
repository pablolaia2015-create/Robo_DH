import os
import json
import requests
import glob
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

def get_secrets():
    """Busca as chaves de forma inteligente no Streamlit ou Termux"""
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
        print("⚠️ ERRO CRÍTICO: Chaves da API (URL_PRODUTOS ou ADMIN_API_SECRET) não encontradas!")
        return

    print(f"\n🚀 PREPARANDO UPLOAD PARA: {api_url}")

    if not os.path.exists(DATA_DIR): 
        print("⚠️ Pasta 'data' não encontrada. Nada para enviar.")
        return

    products = [p for p in os.listdir(DATA_DIR) if os.path.isdir(os.path.join(DATA_DIR, p))]

    if not products:
        print("⚠️ Nenhum produto encontrado na bancada.")
        return

    for product in products:
        path = os.path.join(DATA_DIR, product)
        json_file = os.path.join(path, "data.json")
        
        if not os.path.exists(json_file): continue

        with open(json_file, "r", encoding="utf-8") as f:
            product_data = json.load(f)

        print(f"📤 Enviando Produto: {product_data.get('name')}")

        headers = {"Authorization": f"Bearer {api_key}"}

        # Prepara as Imagens HD para envio
        image_paths = glob.glob(os.path.join(path, "*.jpg"))
        files = []
        
        # O JSON complexo vai como uma string (texto) dentro do pacote
        payload = {
            "product_data": json.dumps(product_data) 
        }
        
        for img_path in image_paths:
            files.append(('photos', (os.path.basename(img_path), open(img_path, 'rb'), 'image/jpeg')))

        try:
            # files= faz com que o Python envie como multipart/form-data automaticamente
            res = requests.post(api_url, data=payload, files=files, headers=headers, timeout=60)

            if res.status_code in [200, 201]:
                print(f"✅ SUCESSO! Produto e {len(image_paths)} fotos enviados para o Alvim.")
            else:
                print(f"⚠️ FALHA NO SERVIDOR ({res.status_code}): {res.text}")
                
        except Exception as e:
            print(f"❌ Erro de Conexão com o servidor do Alvim: {e}")
            
        finally:
            # Segurança: fechar os ficheiros de imagem após o envio
            for _, file_tuple in files:
                file_tuple[1].close()

if __name__ == "__main__":
    start_upload()
