import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
import json
import uuid 
from PIL import Image

def extrair_links(texto_bruto):
    return re.findall(r'(https?://[^\s]+)', texto_bruto)

def processar_produto(url, headers):
    try:
        url = url.strip().split(']')[0].split(',')[0]
        resposta = requests.get(url, headers=headers, timeout=15)
        resposta.raise_for_status()
        site = BeautifulSoup(resposta.text, 'html.parser')
        
        nome_completo = site.title.string.strip().split(' - B&Q')[0] if site.title else "Novo Item"
        nome_limpo = re.sub(r'[^\w\s-]', '', nome_completo)
        nome_pasta = re.sub(r'\s+', ' ', nome_limpo).strip()[:50].strip() 
        
        pasta_destino = os.path.join("Imagens_Produtos", nome_pasta)
        os.makedirs(pasta_destino, exist_ok=True)
        
        # --- PREÇO EM NÚMERO ---
        preco_float = 0.0
        span_preco = site.find('span', {'data-testid': 'product-price'})
        if span_preco:
            nums = re.findall(r'\d+(?:[.,]\d+)?', span_preco.get_text())
            if nums: preco_float = float(nums[0].replace(',', '.'))
                
        # --- ESPECIFICAÇÕES (Com o Filtro Limpo restaurado!) ---
        especificacoes = []
        lista_tamanhos = []
        lista_cores = []
        
        # Palavras para a descrição visual no site
        palavras_chave_descricao = ['Material', 'Finish', 'Height', 'Width', 'Thickness', 'Weight', 'Depth', 'Handle length']
        # Palavras para os arrays de dados
        palavras_tamanho = ['Height', 'Width', 'Thickness', 'Depth', 'Handle length', 'Size']
        palavras_cor = ['Colour', 'Finish', 'Material']
        
        for linha in site.find_all('tr'):
            colunas = linha.find_all(['th', 'td'])
            if len(colunas) == 2:
                chave, valor = colunas[0].get_text(strip=True), colunas[1].get_text(strip=True)
                
                # 1. Filtro: Só adiciona à descrição se for uma informação principal
                if any(p in chave for p in palavras_chave_descricao):
                    especificacoes.append(f"{chave}: {valor}")
                
                # 2. Caça aos tamanhos e cores para o JSON rico
                if any(p in chave for p in palavras_tamanho) and valor not in lista_tamanhos:
                    lista_tamanhos.append(valor)
                if any(p in chave for p in palavras_cor) and valor not in lista_cores:
                    lista_cores.append(valor)

        dropdowns = site.find_all('select')
        for select in dropdowns:
            opcoes = select.find_all('option')
            for op in opcoes:
                texto_opcao = op.get_text(strip=True)
                if "select" not in texto_opcao.lower():
                    if "mm" in texto_opcao.lower() or "cm" in texto_opcao.lower():
                        if texto_opcao not in lista_tamanhos: lista_tamanhos.append(texto_opcao)
                    else:
                        if texto_opcao not in lista_cores: lista_cores.append(texto_opcao)

        if not lista_tamanhos: lista_tamanhos = ["Standard"]
        if not lista_cores: lista_cores = ["Standard"]
            
        # --- CATEGORIA ---
        nome_lower = nome_completo.lower()
        categoria = "General" 
        if "door" in nome_lower or "handle" in nome_lower: categoria = "Doors & Hardware"
        elif "paint" in nome_lower or "brush" in nome_lower: categoria = "Painting"
        elif "screw" in nome_lower or "nail" in nome_lower: categoria = "Fasteners"
            
        # --- IMAGENS ---
        imagens = site.find_all('img')
        fotos_salvas = [] 
        
        for img in imagens:
            link = img.get('src')
            if link and not any(l in link.lower() for l in ['svg', 'gif', 'logo', 'star', 'icon', 'banner']):
                link = urljoin(url, link)
                try:
                    img_data = requests.get(link, headers=headers, timeout=5).content
                    hash_foto = uuid.uuid4().hex + ".jpg"
                    caminho_foto = os.path.join(pasta_destino, hash_foto)
                    
                    with open(caminho_foto, 'wb') as foto: foto.write(img_data)
                    
                    tamanho_adequado = False
                    try:
                        with Image.open(caminho_foto) as img_aberta:
                            if img_aberta.size[0] >= 400 and img_aberta.size[1] >= 400:
                                tamanho_adequado = True
                    except: pass
                        
                    if tamanho_adequado: fotos_salvas.append(hash_foto)
                    else: os.remove(caminho_foto)
                except: pass
                
        # --- O JSON RICO ---
        dados_produto = {
            "name": nome_completo,
            "price": preco_float,
            "qty": "1", 
            "store": "B&Q",
            "description": "\n".join(especificacoes),
            "link": url,
            "category": categoria,
            "sizes": lista_tamanhos, 
            "colors": lista_cores,   
            "photos": fotos_salvas   
        }
        
        with open(os.path.join(pasta_destino, "dados.json"), "w", encoding="utf-8") as f:
            json.dump(dados_produto, f, indent=4, ensure_ascii=False)
            
        return True, nome_pasta
    except Exception as e: return False, str(e)

def iniciar():
    print("\n--- 🤖 DUBLINER PRO (V15 - DESCRIÇÃO LIMPA) ---")
    print("Cole o texto do WhatsApp. Ao terminar, digite OK e Enter.\n")
    linhas = []
    while True:
        try:
            linha = input()
            if linha.upper() == 'OK': break
            linhas.append(linha)
        except EOFError: break
        
    links = extrair_links(" ".join(linhas))
    if not links: return
        
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    for i, link in enumerate(links, 1):
        print(f"[{i}/{len(links)}] Processando...")
        sucesso, resultado = processar_produto(link, headers)
        if sucesso: print(f"✅ Pasta Criada: {resultado}")
        else: print(f"⚠️ Erro: {resultado}")
    print("\n🏁 TUDO FINALIZADO SEM ERROS!")

if __name__ == "__main__":
    iniciar()