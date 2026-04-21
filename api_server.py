from flask import Flask, request, jsonify
import sys
import os

# Adiciona o diretório atual ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src import scraper
from src import uploader

app = Flask(__name__)

@app.route('/api/scrape', methods=['POST'])
def api_scrape():
    data = request.json
    links = data.get('links', [])
    
    if not links:
        return jsonify({"mensagem_telegram": "❌ Erro: Nenhum link recebido."}), 400

    print(f"\n[API] 🤖 A processar {len(links)} link(s) do Telegram...")
    
    # Esta é a mensagem que o Python vai devolver ao Telegram!
    relatorio = f"🤖 **Relatório do Robô**\nTotal: {len(links)} link(s)\n\n"
    
    for url in links:
        url = url.strip() # Limpa espaços vazios
        
        if not url.startswith("http"): # Se não for um link a sério...
            relatorio += f"❌ **Aviso:** O texto recebido não é um link válido.\n"
            continue

        # 🛡️ PROTEÇÃO CONTRA DUPLICADOS (Lê o ficheiro processed_links.txt)
        if os.path.exists("processed_links.txt"):
            with open("processed_links.txt", "r", encoding="utf-8") as f:
                if url in f.read():
                    print("⚠️ Link já processado anteriormente. Saltando...")
                    relatorio += "⚠️ **Duplicado:** Este link já está na tua base de dados.\n"
                    continue

# ⚙️ EXTRAÇÃO
        try:
            scraper.start_extraction(url)
            
            # 🕵️‍♂️ O Dedo-Duro: Vamos ler o JSON que o scraper acabou de criar para ver o preço!
            import json
            preco_zero = False
            
            # Procura o ficheiro data.json na pasta data
            caminho_json = os.path.join(os.path.dirname(__file__), "data", "data.json")
            if os.path.exists(caminho_json):
                with open(caminho_json, "r", encoding="utf-8") as f:
                    dados = json.load(f)
                    # Verifica se o último produto adicionado tem preço 0.0
                    for produto in dados.values():
                        for entrada in produto.get("storeEntries", []):
                            if entrada.get("price") == 0.0:
                                preco_zero = True
            
            if preco_zero:
                relatorio += "⚠️ **Atenção:** Produto extraído, MAS o preço não foi encontrado (está a €0.00). Verifica o link mais tarde!\n"
            else:
                relatorio += "✅ **Sucesso:** Produto extraído com preço válido!\n"
                
        except Exception as e:
            relatorio += f"❌ **Erro:** Falha ao extrair este link.\n"
            
    # Devolve a mensagem final montada para o n8n
    return jsonify({"mensagem_telegram": relatorio}), 200

@app.route('/api/upload', methods=['POST'])
def api_upload():
    print("\n[API] 📤 Ordem de Upload recebida do n8n/Telegram!")
    try:
        uploader.start_upload()
        return jsonify({"mensagem_telegram": "📤 **Upload Concluído!** Os produtos na fila foram enviados para a LisLock."}), 200
    except Exception as e:
        return jsonify({"mensagem_telegram": f"❌ **Erro no Upload:** {str(e)}"}), 500

if __name__ == '__main__':
    print("📡 Servidor da tua API Privada a correr na porta 5000...")
    app.run(host='0.0.0.0', port=5000)
