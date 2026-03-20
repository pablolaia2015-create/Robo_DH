import os
import json
import requests
from dotenv import load_dotenv

# Carrega as chaves do "Cofre" (.env)
load_dotenv()

# 1. Configurações vindas do ficheiro .env
URL_PRODUTOS = os.getenv("URL_PRODUTOS")
URL_OPCOES = os.getenv("URL_OPCOES")
CHAVE_SECRETA = os.getenv("ADMIN_API_SECRET")

HEADERS_SEGURANCA = {
    "Authorization": f"Bearer {CHAVE_SECRETA}"
}

def garantir_opcao_existe(tipo, valor, categoria_pai=""):
    if not valor: return
    dados = {"type": tipo, "value": valor}
    if tipo == "sizes" and categoria_pai: dados["category"] = categoria_pai
    try: 
        requests.post(URL_OPCOES, data=dados, headers=HEADERS_SEGURANCA)
    except: pass 

def iniciar_upload_api():
    print(f"\n--- 🚀 MOTOR DE ENVIO (V17 - MODO COFRE) ---")
    
    # Agora o robô procura as imagens na pasta central de dados
    pasta_principal = os.path.join(os.path.dirname(__file__), "..", "data")
    
    if not os.path.exists(pasta_principal):
        print(f"Aviso: Pasta de dados '{pasta_principal}' vazia.")
        return

    pastas_produtos = [p for p in os.listdir(pasta_principal) if os.path.isdir(os.path.join(pasta_principal, p))]
    
    for pasta in pastas_produtos:
        caminho_pasta = os.path.join(pasta_principal, pasta)
        arquivo_json = os.path.join(caminho_pasta, "dados.json")
        if not os.path.exists(arquivo_json): continue
            
        print(f"▶️ Enviando produto: {pasta}")
        with open(arquivo_json, "r", encoding="utf-8") as f:
            dados_produto = json.load(f)
            
        # ... (Resto da lógica de montagem do payload permanece igual)
        payload_dict = {
            "name": dados_produto.get("name", ""),
            "description": dados_produto.get("description", ""),
            "category": dados_produto.get("category", "Hardware"),
            "color": dados_produto.get("colors", [""])[0],
            "storeEntries": [{
                "storeName": dados_produto.get("store", "B&Q"),
                "link": dados_produto.get("link", ""),
                "price": float(dados_produto.get("price", 0.0)),
                "inventory": [{"size": t, "qty": 1} for t in dados_produto.get("sizes", ["Standard"])]
            }]
        }
        
        dados_api = {"payload": json.dumps(payload_dict)}
        arquivos_para_enviar = []
        
        try:
            lista_fotos = dados_produto.get("photos", [])[:5] 
            for nome_foto in lista_fotos:
                caminho_foto = os.path.join(caminho_pasta, nome_foto)
                if os.path.exists(caminho_foto):
                    arquivos_para_enviar.append(
                        ('photos', (nome_foto, open(caminho_foto, 'rb'), 'image/jpeg'))
                    )

            resposta = requests.post(URL_PRODUTOS, data=dados_api, files=arquivos_para_enviar, headers=HEADERS_SEGURANCA)
            
            if resposta.status_code in [200, 201]:
                print(f"✅ SUCESSO! Guardado no site.")
            else:
                print(f"⚠️ Erro {resposta.status_code}: {resposta.text}")
                
        except Exception as e:
            print(f"⚠️ Erro: {e}")
        finally:
            for _, arquivo_tupla in arquivos_para_enviar: arquivo_tupla[1].close()

if __name__ == "__main__":
    iniciar_upload_api()
