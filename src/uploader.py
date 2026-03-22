import os, json, requests, glob
from dotenv import load_dotenv

load_dotenv()
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

def start_upload():
    api_url = os.getenv("URL_PRODUTOS")
    api_key = os.getenv("ADMIN_API_SECRET")
    
    if not api_url: return

    for product in os.listdir(DATA_DIR):
        path = os.path.join(DATA_DIR, product)
        json_file = os.path.join(path, "data.json")
        if not os.path.exists(json_file): continue

        with open(json_file, "r", encoding="utf-8") as f:
            product_data = json.load(f)

        print(f"📤 Enviando: {product_data.get('name')}")
        payload = {"payload": json.dumps(product_data)}
        headers = {"Authorization": f"Bearer {api_key}"}
        
        files = []
        for img_path in glob.glob(os.path.join(path, "*.jpg")):
            files.append(('photos', (os.path.basename(img_path), open(img_path, 'rb'), 'image/jpeg')))

        try:
            res = requests.post(api_url, data=payload, files=files, headers=headers, timeout=60)
            print(f"✅ RESPOSTA: {res.status_code}")
        except Exception as e: print(f"❌ ERRO: {e}")
        finally:
            for _, f_tuple in files: f_tuple[1].close()
