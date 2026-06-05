from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)  # só mostra erros, esconde os GET
import sys
import os
import json
import threading
import re
import subprocess
import shutil
from datetime import datetime

# --- CONFIGURACAO ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

MEMORIA_DIR = os.path.join(BASE_DIR, "memoria")
DATA_DIR = os.path.join(BASE_DIR, "data")
LINKS_FILE = os.path.join(MEMORIA_DIR, "processed_links.txt")
CATEGORIES_FILE = os.path.join(MEMORIA_DIR, "categories.txt")

os.makedirs(MEMORIA_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

# Logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')

try:
    from src import scraper
    from src import uploader
except Exception as e:
    logging.error(f"Erro ao importar src: {e}")
    scraper = None
    uploader = None

try:
    import requests
except:
    requests = None

app = Flask(__name__, template_folder='templates')
CORS(app)

# Estado thread-safe
estado_upload = {"status": "idle", "mensagem": "", "ultima_atualizacao": None}
estado_lock = threading.Lock()

def set_estado(status, mensagem):
    with estado_lock:
        estado_upload.update({
            "status": status,
            "mensagem": mensagem,
            "ultima_atualizacao": datetime.now().isoformat()
        })

@app.route('/painel', methods=['GET'])
def painel_web():
    return render_template('painel.html')

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "online", "timestamp": datetime.now().isoformat()})

@app.route('/api/categorias', methods=['GET'])
def api_categorias():
    try:
        categorias = scraper.load_categories() if scraper else []
        return jsonify({"categorias": categorias, "total": len(categorias)}), 200
    except Exception as e:
        return jsonify({"erro": str(e), "categorias": []}), 500

@app.route('/api/scrape', methods=['POST'])
def api_scrape():
    data = request.get_json(silent=True) or {}
    
    # ✂️ A TUA CORREÇÃO ESTÁ AQUI: Limpar as quebras de linha invisíveis
    # Juntamos tudo e substituímos os '\n' (Enters) e '\r' por espaços reais
    texto_bruto = json.dumps(data) + " " + str(data.get('url', '')) + " " + str(data.get('urls', ''))
    texto_bruto = texto_bruto.replace('\\n', ' ').replace('\\r', ' ').replace('\n', ' ')
    
    # Agora o Regex consegue separar perfeitamente pelos espaços em branco
    links_brutos = re.findall(r"https?://[^\s'\"<>,]+", texto_bruto)
    links = list(dict.fromkeys([link.rstrip(".,;:)'\"") for link in links_brutos]))
    
    if not links:
        return jsonify({"mensagem_telegram": "❌ Erro: Nenhum link valido detectado."}), 400

    # --- INTELIGÊNCIA DE DESTINO ---
    # Verifica se algum dos links pertence a Portugal
    is_portugal = any((".pt" in u or "leroymerlin" in u or "obramat" in u) for u in links)
    destino_nome = "🇵🇹 Lisbon" if is_portugal else "🇮🇪 Dublin"

    # --- Mensagem 1 ---
    relatorio = f"🤖 Processing started, Boss!\n"
    relatorio += f"🔗 Links received: {len(links)}\n"
    relatorio += f"🌍 Target Destination: {destino_nome}\n\n"
    relatorio += f"Putting on the Mechanical Suit. Please wait a few seconds...\n\n"
    
    processados = 0
    processed_set = set()
    if os.path.exists(LINKS_FILE):
        with open(LINKS_FILE, "r", encoding="utf-8") as f:
            processed_set = set(line.strip() for line in f)
    
    for url in links:
        url = url.strip()
        if url in processed_set:
            relatorio += f"⚠ Duplicate: {url[:50]}...\n"
            continue
        try:
            if scraper:
                scraper.start_extraction(url)
                with open(LINKS_FILE, "a", encoding="utf-8") as f:
                    f.write(url + "\n")
                processados += 1
            else:
                relatorio += f"❌ Error: Scraper module not loaded\n"
        except Exception as e:
            logging.exception("Scrape error")
            relatorio += f"❌ Error: {str(e)[:50]}\n"
    
    # --- Mensagem 2 ---
    relatorio += f"\n🤖 Bot Report\n"
    relatorio += f"Total processing: {len(links)} link(s)\n"
    if processados > 0:
        relatorio += f"✅ Success ({destino_nome}): Product extracted with a valid price!\n"
    else:
        relatorio += f"⚠ No new products processed\n"
    
    return jsonify({"mensagem_telegram": relatorio, "processados": processados}), 200

@app.route('/api/upload', methods=['POST'])
def api_upload():
    data = request.get_json(silent=True) or {}
    chat_id = data.get('chat_id')
    
    with estado_lock:
        if estado_upload["status"] == "processing":
            return jsonify({"mensagem_telegram": "⏳ Upload ja em andamento..."}), 429
    
    set_estado("processing", "⏳ Processing upload...")
    
    def upload_bg(cid):
        try:
            if uploader:
                uploader.start_upload()
                set_estado("success", "✅ **SUCCESS:** Upload complete!")
            else:
                set_estado("error", "❌ Uploader module not loaded")
        except Exception as e:
            logging.exception("Upload error")
            set_estado("error", f"❌ **UPLOAD ERROR:** {str(e)}")
        
        token = os.getenv("TELEGRAM_TOKEN")
        if cid and token and requests:
            try:
                url = f"https://api.telegram.org/bot{token}/sendMessage"
                requests.post(url, json={"chat_id": cid, "text": estado_upload["mensagem"], "parse_mode": "Markdown"}, timeout=10)
            except Exception as e:
                logging.error(f"Telegram notify fail: {e}")
    
    threading.Thread(target=upload_bg, args=(chat_id,), daemon=True).start()
    return jsonify({"mensagem_telegram": "⏳ Processing upload in background..."}), 202

@app.route('/api/upload/status', methods=['GET'])
def get_status():
    with estado_lock:
        return jsonify(estado_upload)

@app.route('/api/upload/reset', methods=['GET'])
def reset_status():
    set_estado("idle", "")
    return jsonify({"status": "ok"})

@app.route('/api/aspirador', methods=['POST'])
def api_aspirador():
    data = request.get_json(silent=True) or {}
    url_categoria = data.get('url')
    if not url_categoria:
        return jsonify({"erro": "Category URL is required"}), 400
    
    try:
        links = []
        if scraper and hasattr(scraper, 'aspirar_links'):
            links = scraper.aspirar_links(url_categoria)
        elif scraper and hasattr(scraper, 'extract_links_from_category'):
            links = scraper.extract_links_from_category(url_categoria)
        else:
            if requests:
                r = requests.get(url_categoria, timeout=15)
                # CORREÇÃO SINTAXE: Aspas duplas escapadas dentro da string raw (\")
                links = re.findall(r"https?://[^\s'\"]+/produto[^\s'\"]*", r.text)
        
        links = list(dict.fromkeys(links))[:200]
        return jsonify({"mensagem": f"🧲 {len(links)} links found", "links": links}), 200
    except Exception as e:
        logging.exception("Vacuum")
        return jsonify({"erro": str(e)}), 500

def run_git(cmd):
    try:
        result = subprocess.run(cmd, cwd=BASE_DIR, shell=True, capture_output=True, text=True, timeout=60)
        return result.returncode == 0, result.stdout + result.stderr
    except Exception as e:
        return False, str(e)

@app.route('/api/github/push', methods=['POST'])
def github_push():
    ok, out = run_git("git add . && git commit -m 'Auto-push via Web Panel' && git push")
    return jsonify({"sucesso": ok, "mensagem": "☁ Push executed!" if ok else "❌ Push failed", "log": out[:1000]})

@app.route('/api/github/pull', methods=['POST'])
def github_pull():
    ok, out = run_git("git pull")
    return jsonify({"sucesso": ok, "mensagem": "☁ Pull executed!" if ok else "❌ Pull failed", "log": out[:1000]})

@app.route('/api/limpeza/total', methods=['POST'])
def limpeza_total():
    try:
        if os.path.exists(DATA_DIR):
            shutil.rmtree(DATA_DIR)
            os.makedirs(DATA_DIR)
        return jsonify({"mensagem": "✅ Full cleanup completed!"})
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route('/api/limpeza/link', methods=['POST'])
def limpeza_link():
    data = request.get_json(silent=True) or {}
    url = data.get('url', '').strip()
    if not url:
        return jsonify({"erro": "URL is required"}), 400
    
    if os.path.exists(LINKS_FILE):
        with open(LINKS_FILE, "r", encoding="utf-8") as f:
            linhas = [l for l in f if url not in l]
        with open(LINKS_FILE, "w", encoding="utf-8") as f:
            f.writelines(linhas)
    
    pasta_nome = re.sub(r'[^a-zA-Z0-9]', '_', url)[:50]
    pasta_path = os.path.join(DATA_DIR, pasta_nome)
    if os.path.exists(pasta_path):
        shutil.rmtree(pasta_path)
    
    return jsonify({"mensagem": f"🗑 Link removed: {url[:40]}..."})

@app.route('/api/refresh', methods=['POST'])
def api_refresh():
    try:
        import importlib
        if scraper:
            importlib.reload(scraper)
        if uploader:
            importlib.reload(uploader)
        return jsonify({"mensagem": "🔄 Scraper code reloaded!"})
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route('/api/acao', methods=['POST'])
def api_acao():
    data = request.get_json(silent=True) or {}
    acao = data.get('acao')
    
    mapa = {
        'limpeza': limpeza_total,
        'github_push': github_push,
        'github_pull': github_pull,
        'refresh': api_refresh,
    }
    
    if acao in mapa:
        return mapa[acao]()
    
    return jsonify({"erro": "Unknown action"}), 400

# === MAGIA DA CLOUD AQUI ===
if __name__ == '__main__':
    # Na Cloud (Render, Heroku, etc), eles injetam a variável 'PORT'.
    # Se não houver 'PORT' (como no teu PC), ele usa a 5000 por defeito.
    port = int(os.environ.get('PORT', 5000))
    
    print(f"--- API Server v3 (Cloud Ready) running on port {port} ---")
    if port == 5000:
        print("👉 Local: http://127.0.0.1:5000/painel")
        
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)