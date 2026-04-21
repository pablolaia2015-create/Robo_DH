import os, json, requests, glob, shutil
from dotenv import load_dotenv

load_dotenv()
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
SENT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data_enviados")

def start_upload():
    # Garante que a pasta de arquivo existe antes de começarmos
    os.makedirs(SENT_DIR, exist_ok=True)

    for product in os.listdir(DATA_DIR):
        path = os.path.join(DATA_DIR, product)
        
        # Ignora se for um ficheiro solto, foca só nas pastas
        if not os.path.isdir(path): continue

        json_file = os.path.join(path, "data.json")
        if not os.path.exists(json_file): continue

        # Lemos o JSON primeiro para descobrir de que loja é
        with open(json_file, "r", encoding="utf-8") as f:
            product_data = json.load(f)

        # 🧠 CÉREBRO DE ROTEAMENTO NO UPLOADER
        try:
            store_name = product_data["storeEntries"][0]["storeName"]
        except:
            store_name = "Desconhecida"

        if store_name == "Leroy Merlin":
            api_url = "https://lislock.pt/api/admin/supplies"
            prefixo = "🇵🇹 LISBOA"
        else:
            api_url = "https://dublinerhandyman.ie/api/admin/supplies"
            prefixo = "🇮🇪 DUBLIN"

        print(f"📤 [{prefixo}] A enviar: {product_data.get('name')}")
        
        payload = {"payload": json.dumps(product_data)}
        # A API key agora pode ser a mesma para os dois sites, assumindo que o Alvim usa a mesma senha nos dois. 
        # Se forem senhas diferentes, avisa-me!
        api_key = os.getenv("ADMIN_API_SECRET")
        headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        
        files = []
        for img_path in glob.glob(os.path.join(path, "*.jpg")):
            files.append(('photos', (os.path.basename(img_path), open(img_path, 'rb'), 'image/jpeg')))

        try:
            res = requests.post(api_url, data=payload, files=files, headers=headers, timeout=60)
            print(f"✅ RESPOSTA: {res.status_code}")
            
            # Fechamos as fotos IMEDIATAMENTE para o Windows soltar a pasta
            for _, f_tuple in files: f_tuple[1].close()
            
            # Se a resposta for 200 ou 201 (Sucesso ou Criado), movemos a pasta!
            if res.status_code in [200, 201]:
                dest_path = os.path.join(SENT_DIR, product)
                if os.path.exists(dest_path):
                    shutil.rmtree(dest_path) # Apaga se já existir uma versão velha lá
                shutil.move(path, SENT_DIR)
                print(f"📦 Sucesso! Pasta movida para o arquivo morto (data_enviados).\n")
            else:
                print(f"⚠️ Falha no envio. A pasta continuará na fila.\nDetalhe: {res.text}\n")

        except Exception as e: 
            print(f"❌ ERRO: {e}\n")
        finally:
            for _, f_tuple in files:
                try: f_tuple[1].close() 
                except: pass