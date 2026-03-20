import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()
API_URL = os.getenv("URL_PRODUTOS")
API_KEY = os.getenv("ADMIN_API_SECRET")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

def start_upload():
    print(f"\n🚀 UPLOADING TO SITE: {API_URL}")
    if not os.path.exists(DATA_DIR): return

    products = [p for p in os.listdir(DATA_DIR) if os.path.isdir(os.path.join(DATA_DIR, p))]
    
    for product in products:
        path = os.path.join(DATA_DIR, product)
        json_file = os.path.join(path, "data.json")
        if not os.path.exists(json_file): continue

        with open(json_file, "r", encoding="utf-8") as f:
            payload = json.load(f)

        print(f"📤 Sending: {payload['name']}")
        
        # Pega as fotos da pasta (conforme imagem Item Photos 0/5)
        photos = [('photos[]', (img, open(os.path.join(path, img), 'rb'), 'image/jpeg')) 
                 for img in os.listdir(path) if img.lower().endswith(('.jpg', '.png'))]

        try:
            headers = {"Authorization": f"Bearer {API_KEY}"}
            # Enviamos os dados e as fotos juntos
            res = requests.post(API_URL, data=payload, files=photos, headers=headers)
            
            if res.status_code in [200, 201]:
                print(f"✅ {product}: Success!")
            else:
                print(f"⚠️ {product}: Failed ({res.status_code})")
        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            for p in photos: p[1][1].close()
