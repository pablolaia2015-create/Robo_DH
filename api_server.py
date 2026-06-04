from flask import Flask, request, jsonify
import sys
import os
import json
import threading
import re # Essential library to find links in the middle of text

# --- CONFIGURAÇÃO DE CAMINHOS E GPS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

MEMORIA_DIR = os.path.join(BASE_DIR, "memoria")
LINKS_FILE = os.path.join(MEMORIA_DIR, "processed_links.txt")
# --------------------------------------

from src import scraper
from src import uploader

app = Flask(__name__)

@app.route('/api/scrape', methods=['POST'])
def api_scrape():
    data = request.json
    
    # 1. Transform everything into raw text and replace literal line breaks ('\n') with spaces
    texto_bruto = str(data).replace('\\n', ' ').replace('\n', ' ')
    
    # 2. Universal Scanner: Catches everything starting with http:// or https://
    # until it finds a space, quote, comma, or formatting character.
    links_brutos = re.findall(r'(https?://[^\s\'"\\,]+)', texto_bruto)
    
    # 3. Final Cleanup: Removes unwanted characters at the end of the link (e.g., periods)
    links = [link.rstrip(".,;:)'\"") for link in links_brutos]
    
    # Remove duplicates
    links = list(set(links))
    
    if not links:
        return jsonify({"mensagem_telegram": "❌ Error: No valid links detected in the message."}), 400

    print(f"\n[API] 🤖 Processing {len(links)} link(s) from Telegram in BATCH...")
    
    relatorio = f"🤖 **Bot Report**\nTotal processing: {len(links)} link(s)\n\n"
    
    for url in links:
        url = url.strip() 
        
        if ".pt" in url or "leroymerlin.pt" in url or "obramat.pt" in url:
            destino = "🇵🇹 Lisbon"
        else:
            destino = "🇮🇪 Dublin"

        # Verificação de duplicados usando o novo GPS da memória
        if os.path.exists(LINKS_FILE):
            with open(LINKS_FILE, "r", encoding="utf-8") as f:
                if url in f.read():
                    print("⚠️ Link already processed previously. Skipping...")
                    relatorio += f"⚠️ **Duplicate ({destino}):** This link is already in the database.\n"
                    continue

        try:
            # The extraction itself
            scraper.start_extraction(url)
            
            preco_zero = False
            caminho_data_dir = os.path.join(BASE_DIR, "data")
            if os.path.exists(caminho_data_dir):
                for nome_pasta in os.listdir(caminho_data_dir):
                    pasta_produto = os.path.join(caminho_data_dir, nome_pasta)
                    if os.path.isdir(pasta_produto):
                        json_file = os.path.join(pasta_produto, "data.json")
                        if os.path.exists(json_file):
                            try:
                                with open(json_file, "r", encoding="utf-8") as f:
                                    produto_dados = json.load(f)
                                    for entrada in produto_dados.get("storeEntries", []):
                                        if entrada.get("link") == url and entrada.get("price") == 0.0:
                                            preco_zero = True
                            except: pass
            
            if preco_zero:
                relatorio += f"⚠️ **Attention ({destino}):** Product extracted, BUT the price is €0.00. Please check!\n"
            else:
                relatorio += f"✅ **Success ({destino}):** Product extracted with a valid price!\n"
                
        except Exception as e:
            relatorio += f"❌ **Error ({destino}):** Failed to extract this link.\n"
            
    return jsonify({"mensagem_telegram": relatorio}), 200

@app.route('/api/upload', methods=['POST'])
def api_upload():
    print("\n[API] 📤 Upload command received from n8n/Telegram!")
    
    data = request.json or {}
    chat_id = data.get('chat_id')
    
    def upload_em_segundo_plano(cid):
        try:
            print("⏳ Starting background upload...")
            uploader.start_upload()
            print("✅ Upload complete!")
            mensagem_final = "✅ **SUCCESS:** The upload is complete and the products are now online!"
        except Exception as e:
            print(f"❌ Upload error: {e}")
            mensagem_final = f"❌ **UPLOAD ERROR:** Failed to process the products. Detail: {e}"
            
        token = os.getenv("TELEGRAM_TOKEN")
        if cid and token:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            import requests
            requests.post(url, json={"chat_id": cid, "text": mensagem_final, "parse_mode": "Markdown"})

    thread = threading.Thread(target=upload_em_segundo_plano, args=(chat_id,))
    thread.start()

    mensagem_inicial = "⏳ **Processing upload...** I'll send a confirmation when it's done."
    return jsonify({"mensagem_telegram": mensagem_inicial}), 200

# === THE MAGIC HAPPENS HERE ===
if __name__ == '__main__':
    print("--- API Server Active on port 5000 ---")
    app.run(host='0.0.0.0', port=5000)