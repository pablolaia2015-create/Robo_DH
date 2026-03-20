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
    print(f"\n🚀 STARTING REAL UPLOAD TO: {API_URL}")
    
    if not os.path.exists(DATA_DIR):
        print("❌ Error: 'data' folder not found.")
        return

    products = [p for p in os.listdir(DATA_DIR) if os.path.isdir(os.path.join(DATA_DIR, p))]
    
    for product in products:
        path = os.path.join(DATA_DIR, product)
        json_file = os.path.join(path, "data.json")
        
        if not os.path.exists(json_file): continue

        print(f"📤 Uploading: {product}")
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                product_data = json.load(f)

            headers = {"Authorization": f"Bearer {API_KEY}"}
            payload = {"payload": json.dumps(product_data)}
            
            # Envio real
            res = requests.post(API_URL, data=payload, headers=headers)
            
            if res.status_code in [200, 201]:
                print(f"✅ {product}: Success!")
            else:
                print(f"⚠️ {product}: Failed (Status {res.status_code})")
        except Exception as e:
            print(f"❌ Error in {product}: {e}")

if __name__ == "__main__":
    start_upload()
