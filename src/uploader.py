import os, json, requests, glob, shutil, time
from dotenv import load_dotenv
from PIL import Image

load_dotenv()
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
SENT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data_enviados")

# --- NOVA FUNÇÃO: SEGURANÇA DE IMAGENS E ANTI-ERRO 500 ---
def comprimir_imagem_se_necessario(caminho_imagem):
    """
    Tenta abrir a imagem. Se for HTML disfarçado de imagem ou corrompida, 
    devolve False para o robô não enviar "lixo" ao WordPress.
    """
    tamanho_atual = os.path.getsize(caminho_imagem)
    if tamanho_atual == 0:
        return False # Ficheiro vazio
        
    try:
        with Image.open(caminho_imagem) as img:
            img.verify() # Confirma se a estrutura interna é mesmo de uma imagem
            
        with Image.open(caminho_imagem) as img:
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            
            # Comprime para limites da web (Evita o Erro 500 do Alvim)
            max_size = (1200, 1200)
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            img.save(caminho_imagem, "JPEG", quality=80, optimize=True)
            
        return True # Imagem é válida e está pronta!
        
    except Exception as e:
        print(f"   ⚠️ Imagem corrompida ou falsa ignorada ({os.path.basename(caminho_imagem)}): {e}")
        return False
# ---------------------------------------------

def mover_com_tentativas(src, dst, max_tentativas=5):
    for i in range(max_tentativas):
        try:
            if os.path.exists(dst):
                shutil.rmtree(dst)
            shutil.move(src, dst)
            return True
        except PermissionError:
            print(f"   ⏳ Sistema a bloquear a pasta. A aguardar... (Tentativa {i+1}/{max_tentativas})")
            time.sleep(2)
    return False

def start_upload():
    os.makedirs(SENT_DIR, exist_ok=True)

    for product in os.listdir(DATA_DIR):
        path = os.path.join(DATA_DIR, product)
        if not os.path.isdir(path): continue

        json_file = os.path.join(path, "data.json")
        if not os.path.exists(json_file): continue

        with open(json_file, "r", encoding="utf-8") as f:
            product_data = json.load(f)

        try:
            store_name = product_data["storeEntries"][0]["storeName"]
            product_link = product_data["storeEntries"][0]["link"]
        except:
            store_name = "Desconhecida"
            product_link = ""

        if store_name == "Leroy Merlin" or ".pt" in product_link:
            api_url = "https://lislock.pt/api/admin/supplies"
            prefixo = "🇵🇹 LISBOA"
        else:
            api_url = "https://dublinerhandyman.ie/api/admin/supplies"
            prefixo = "🇮🇪 DUBLIN"

        print(f"📤 [{prefixo}] A enviar: {product_data.get('name')}")
        
        payload = {"payload": json.dumps(product_data)}
        api_key = os.getenv("ADMIN_API_SECRET")
        headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        
        files = []
        
        try:
            for img_path in glob.glob(os.path.join(path, "*.jpg")):
                # SÓ ADICIONA A FOTO SE O NOSSO 'SEGURANÇA' DER LUZ VERDE
                if comprimir_imagem_se_necessario(img_path): 
                    
                    # --- O TRUQUE DE MESTRE ANTI WINERROR 5 ---
                    # Lemos o ficheiro para a memória e o Python fecha-o NA HORA
                    with open(img_path, 'rb') as f:
                        img_data = f.read()
                    
                    # Passamos apenas a memória (img_data) e não o ficheiro bloqueado
                    files.append(('photos', (os.path.basename(img_path), img_data, 'image/jpeg')))
                    # ------------------------------------------

            if not files:
                print("   ⚠️ Nenhuma imagem válida encontrada. A enviar produto sem galeria...")

            res = requests.post(api_url, data=payload, files=files, headers=headers, timeout=120)

            print(f"✅ RESPOSTA: {res.status_code}")
            
            if res.status_code in [200, 201]:
                sucesso = mover_com_tentativas(path, os.path.join(SENT_DIR, product))
                if sucesso:
                    print(f"📦 Sucesso! Pasta movida para o arquivo morto (data_enviados).\n")
                else:
                    print(f"⚠️ Online! Mas não movi a pasta porque o Windows não deixou.\n")
            else:
                print(f"⚠️ Falha no envio. Erro do Servidor do Site.\nDetalhe do Erro: {res.text[:200]}\n")

        except Exception as e: 
            print(f"❌ ERRO DE CONEXÃO: {e}\n")