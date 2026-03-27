import os, json, requests, glob, shutil
from dotenv import load_dotenv

load_dotenv()
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
# NOVA LINHA: Definimos a pasta de destino para os que derem sucesso
SENT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data_enviados")

def start_upload():
    api_url = os.getenv("URL_PRODUTOS")
    api_key = os.getenv("ADMIN_API_SECRET")
    
    if not api_url: return

    # NOVA LINHA: Garante que a pasta de arquivo existe antes de começarmos
    os.makedirs(SENT_DIR, exist_ok=True)

    for product in os.listdir(DATA_DIR):
        path = os.path.join(DATA_DIR, product)
        
        # NOVA LINHA DE SEGURANÇA: Ignora se for um ficheiro solto, foca só nas pastas
        if not os.path.isdir(path): continue

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
            
            # --- INÍCIO DA NOVA LÓGICA DE MOVER ---
            # 1. Fechamos as fotos IMEDIATAMENTE para o Windows soltar a pasta
            for _, f_tuple in files: f_tuple[1].close()
            
            # 2. Se a resposta foi 200 (Sucesso), movemos a pasta!
            if res.status_code == 200:
                dest_path = os.path.join(SENT_DIR, product)
                if os.path.exists(dest_path):
                    shutil.rmtree(dest_path) # Apaga se já existir uma versão velha lá
                shutil.move(path, SENT_DIR)
                print(f"📦 Sucesso! Pasta movida para o arquivo morto (data_enviados).")
            # --- FIM DA NOVA LÓGICA ---

        except Exception as e: 
            print(f"❌ ERRO: {e}")
        finally:
            # Fecho de segurança caso o código quebre antes de chegar à linha de mover
            for _, f_tuple in files:
                try: f_tuple[1].close() 
                except: pass