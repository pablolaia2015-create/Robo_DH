import os, sys, time, shutil, importlib
import cloudscraper
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# --- CONFIGURAÇÃO DE CAMINHOS E GPS (Pasta 'memoria') ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MEMORIA_DIR = os.path.join(BASE_DIR, "memoria")

# Garante que a pasta memoria existe
os.makedirs(MEMORIA_DIR, exist_ok=True)

sys.path.append(os.path.join(BASE_DIR, 'src'))

# Importação Inicial (Pode ser recarregada mais tarde)
import src.scraper as scraper
import src.uploader as uploader

# Define os caminhos dos ficheiros de texto para o novo GPS
LINKS_FILE = os.path.join(MEMORIA_DIR, "processed_links.txt")
LOTE_FILE = os.path.join(MEMORIA_DIR, "links_em_lote.txt")

def limpar_tela():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    limpar_tela()
    print("\n" + "═"*50)
    print(" 🤖 DUBLINER HANDYMAN ROBOT - PAINEL DE COMANDO")
    print(" 🌟 VERSION V28.4 SUPER PRO (GPS + API INTEGRADA)")
    print("═"*50 + "\n")

# --- NOVA FUNÇÃO: O ASPIRADOR DE CATEGORIAS TURBINADO (FATO MECÂNICO) ---
def extrair_links_da_categoria(url_categoria):
    print("\n⏳ A ligar o 'Aspirador Turbinado' (Fato Mecânico)...")
    print("💡 Ele vai abrir o Chrome sozinho para garantir que carrega todos os produtos escondidos!")
    
    # Preparar o Fato Mecânico
    options = uc.ChromeOptions()
    options.add_argument("--window-size=1920,1080")
    # Nota: Não usamos headless para evitar que o Cloudflare nos bloqueie de imediato
    driver = uc.Chrome(options=options, version_main=148)
    
    try:
        driver.get(url_categoria)
        print("⏳ A dar 8 segundos para o site carregar os produtos e passar a segurança...")
        time.sleep(8)

        # Clicar nos cookies se aparecerem (ajuda a desbloquear a página)
        try:
            botoes = driver.find_elements(By.XPATH, "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'aceitar')]")
            if botoes:
                botoes[0].click()
                time.sleep(2)
        except: pass

        # Fazer SCROLL automático para carregar os produtos mais abaixo (Lazy Loading)
        print("📜 A fazer scroll para baixo para revelar todos os itens (Aguarde)...")
        last_height = driver.execute_script("return document.body.scrollHeight")
        for _ in range(6): # Tenta fazer scroll 6 vezes
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2.5)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break # Chegou ao fim da página
            last_height = new_height

        # Agora que tudo carregou, sugamos o HTML
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        links_encontrados = set()

        # Procurar todos os links na página carregada
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            full_url = urljoin(url_categoria, href)
            
            # FILTRO UNIVERSAL: Funciona para Obramat (e já meio caminho andado para outras lojas)
            if "/produtos/" in full_url and full_url.endswith(".html"):
                links_encontrados.add(full_url)

        if links_encontrados:
            with open(LOTE_FILE, "w", encoding="utf-8") as f:
                for link in links_encontrados:
                    f.write(link + "\n")
            print(f"\n✅ SUCESSO ABSOLUTO! {len(links_encontrados)} links de produtos guardados no ficheiro 'links_em_lote.txt'.")
            print("💡 Dica: Agora abre o ficheiro, copia os links e manda para o Telegram!")
        else:
            print("\n⚠️ A página carregou, fiz scroll, mas não encontrei links com a estrutura de produto.")
            
    except Exception as e:
        print(f"\n❌ Ocorreu um erro no Aspirador: {e}")
    finally:
        print("🚪 Fechando o Chrome do Aspirador...")
        driver.quit()

# --- MENU PRINCIPAL ---
def menu_principal():
    while True:
        print_header()
        print("✅ ESCOLHA UMA AÇÃO:")
        print("  [ 1 ] 🎯 SCRAPE ÚNICO (Extrair um Produto)")
        print("  [ 2 ] 🚀 SCRAPE EM LOTE (Buffer Interativo)")
        print("  [ 3 ] 📤 UPLOAD PARA O SITE (ALVIM)")
        print("  [ 4 ] 📂 VER CATEGORIAS APRENDIDAS")
        print("  [ 5 ] ☁️  CLOUD PUSH (Guardar no GitHub)")
        print("  [ 6 ] ☁️  CLOUD PULL (Baixar do GitHub)")
        print("  [ 7 ] 🗑️  APAGAR LINK E PASTA (Limpeza Total)")
        print("  [ 8 ] 🔄 REFRESH (Recarregar Código do Scraper)")
        print("  [ 9 ] 🧲 ASPIRADOR DE LINKS (Extrair de uma Categoria)")
        print("  [ 10] 🌐 LIGAR SERVIDOR API (Receber do Telegram)")
        print("  [ 0 ] 👋 SAIR")
        print("-" * 50)

        escolha = input("👉 Digite uma opção (0-10): ").strip()

        if escolha == "1":
            print("\n" + "*"*40)
            print("🎯 MODO SCRAPER ÚNICO ATIVO")
            link = input("🔗 COLE O LINK DO PRODUTO: ").strip()
            if link:
                print("\n🕵️‍♂️ A iniciar extração furtiva...")
                scraper.start_extraction(link)
            else:
                print("\n❌ Erro: Nenhum link foi colado.")
            input("\n🔙 Pressione ENTER para voltar ao menu...")

        elif escolha == "2":
            print("\n" + "*"*40)
            print("🚀 MODO SCRAPER EM LOTE ATIVO")
            print("🔗 Cole os links um por um e pressione ENTER.")
            print("✅ Quando terminar, escreva 'ok' ou 'OK' e pressione ENTER para arrancar!")
            print("-" * 40)
            
            links_em_espera = []
            
            while True:
                entrada = input(f"[{len(links_em_espera)} links prontos] 👉 ").strip()
                
                if entrada.lower() == 'ok':
                    break
                elif not entrada:
                    continue
                else:
                    links_em_espera.append(entrada)
                    
            print("-" * 40)
            
            if links_em_espera:
                print(f"🚦 A arrancar a extração de {len(links_em_espera)} links...")
                for i, link in enumerate(links_em_espera, 1):
                    print(f"\n[{i}/{len(links_em_espera)}] A processar: {link}")
                    scraper.start_extraction(link)
                    time.sleep(2)
                print("\n✅ Lote concluído!")
            else:
                print("⚠️ Ação cancelada ou nenhum link foi colado.")
                
            input("\n🔙 Pressione ENTER para voltar ao menu...")

        elif escolha == "3":
            print("\n" + "^"*40)
            print("📤 MODO UPLOAD ATIVO")
            print("A iniciar envio dos produtos na pasta 'data' para o Alvim...")
            uploader.start_upload()
            input("\n🔙 Pressione ENTER para voltar ao menu...")

        elif escolha == '4':
            print("\n" + "📂"*20)
            try:
                categorias = scraper.load_categories()
                print("\n📚 O robô já conhece estas categorias:")
                for i, cat in enumerate(categorias, 1):
                    print(f"  {i}. {cat}")
            except Exception as e:
                print(f"⚠️ Erro ao carregar categorias: {e}")
            input("\n🔙 Pressione ENTER para voltar ao menu...")

        elif escolha == "5":
            print("\n" + "☁️"*15)
            print("A iniciar Backup para o GitHub...")
            os.system("git add .")
            os.system('git commit -m "Auto-backup V28.4 pelo Menu do Robô"')
            os.system("git push")
            print("✅ Backup concluído com sucesso!")
            input("\n🔙 Pressione ENTER para voltar ao menu...")

        elif escolha == "6":
            print("\n" + "☁️"*15)
            print("A procurar atualizações no GitHub...")
            os.system("git pull")
            print("✅ Atualização concluída!")
            input("\n🔙 Pressione ENTER para voltar ao menu...")

        elif escolha == "7":
            print("\n" + "🗑️"*20)
            print("MODO APAGAR LINK DA MEMÓRIA")
            link_to_delete = input("🔗 COLE O LINK QUE DESEJA APAGAR: ").strip()
            
            if link_to_delete and os.path.exists(LINKS_FILE):
                with open(LINKS_FILE, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                
                apagado = False
                with open(LINKS_FILE, "w", encoding="utf-8") as f:
                    for line in lines:
                        if line.strip() == link_to_delete:
                            apagado = True
                        else:
                            f.write(line)
                
                if apagado:
                    print("✅ Link apagado com sucesso do ficheiro de memória.")
                    
                    limpar_pasta = input("⚠️ Queres apagar TODOS os produtos na pasta 'data' para recomeçar limpo? (s/n): ").strip().lower()
                    
                    if limpar_pasta == 's':
                        pasta_data = os.path.join(BASE_DIR, "data")
                        if os.path.exists(pasta_data):
                            shutil.rmtree(pasta_data) 
                            os.makedirs(pasta_data)
                            print("🧹 Pasta 'data' limpa com sucesso! O robô está pronto para um novo começo.")
                        else:
                            print("A pasta 'data' não foi encontrada.")
                    else:
                        print("A pasta 'data' não foi alterada.")
                        print("⚠️ Não te esqueças de apagar manualmente a pasta do produto que estás a testar para evitar conflitos!")
                else:
                    print("⚠️ O link não foi encontrado na memória.")
            else:
                print("❌ Erro: Link vazio ou ficheiro de memória não existe.")
            input("\n🔙 Pressione ENTER para voltar ao menu...")
            
        elif escolha == "8":
            print("\n🔄 A recarregar o código do Scraper e Uploader...")
            try:
                importlib.reload(scraper)
                importlib.reload(uploader)
                print("✅ Sistemas atualizados com sucesso! Prontos a rodar com as novas alterações.")
            except Exception as e:
                print(f"❌ Erro ao recarregar os ficheiros: {e}")
            input("\n🔙 Pressione ENTER para voltar ao menu...")

        elif escolha == "9":
            print("\n" + "🧲"*20)
            print("MODO ASPIRADOR DE LINKS ATIVO")
            url_alvo = input("🔗 COLE O LINK DA PÁGINA DE CATEGORIA: ").strip()
            if url_alvo:
                extrair_links_da_categoria(url_alvo)
            else:
                print("❌ Link inválido ou vazio.")
            input("\n🔙 Pressione ENTER para voltar ao menu...")

        # --- A NOVA OPÇÃO 10: LIGAR SERVIDOR API ---
        elif escolha == "10":
            print("\n" + "🌐"*20)
            print("A iniciar o Servidor API...")
            print("⚠️ ATENÇÃO: O menu ficará pausado enquanto o servidor estiver a ouvir o Telegram.")
            print("🛑 Para desligar o servidor e voltar a este menu, pressiona [ CTRL + C ]")
            print("-" * 50)
            try:
                # Chama o script do servidor
                os.system("python api_server.py")
            except KeyboardInterrupt:
                pass # Captura o Ctrl+C para não rebentar o menu
            print("\n🛑 Servidor desligado. A voltar ao menu principal...")
            time.sleep(1)

        elif escolha == "0":
            print("\n👋 A desligar os motores. Adeus, Master! Encerrando com qualidade.")
            time.sleep(1)
            break
            
        else:
            print("\n❌ Opção inválida. Tente novamente.")
            time.sleep(1.5)

# --- INICIAR PROGRAMA ---
if __name__ == "__main__":
    menu_principal()