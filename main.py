import os, sys, time
# Adiciona src ao caminho para podermos importar os módulos
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))
from scraper import start_extraction
from uploader import start_upload

def print_header():
    """Desenha o cabeçalho bonitinho apenas UMA vez."""
    # os.system('clear') # Opcional: limpa o ecrã ao iniciar
    print("\n" + "="*40)
    print("         DUBLINER HANDYMAN ROBOT")
    print("             VERSION V27.3.1 GOLD")
    print("="*40 + "\n")

def print_menu():
    """Mostra apenas as opções de ação."""
    print("✅ ESCOLHA UMA AÇÃO:")
    print("   [1] 🕷️ SCRAPE PRODUTO (B&Q)")
    print("   [2] 📤 UPLOAD PARA O SITE (ALVIM)")
    print("   [0] 👋 SAIR")
    print("-" * 40)

def main():
    print_header() # Chamado apenas UMA vez aqui

    while True:
        print_menu() # As opções aparecem a cada loop
        choice = input("👉 Digite uma opção: ").strip()

        if choice == "1":
            print("\n" + "*"*40)
            print("🕷️ MODO SCRAPER B&Q ATIVO")
            link = input("🔗 COLE O LINK DA B&Q: ").strip()
            
            # PROTEÇÃO: Verifica se o link está vazio
            if not link:
                print("\n❌ Erro: Nenhum link foi colado. Voltando ao menu...")
                print("*"*40 + "\n")
                continue # Recomeça o loop sem tentar extrair

            print("\n🕵️‍♂️ Iniciando extração furtiva...")
            start_extraction(link)
            print("\n" + "*"*40 + "\n")

        elif choice == "2":
            print("\n" + "^"*40)
            print("📤 MODO UPLOAD ATIVO")
            print("\nStarting uploader...")
            # start_upload() # Comentado porque você disse 'esquece Alvim' hoje
            print("Upload pulado. Foco no código local.")
            print("\n" + "^"*40 + "\n")

        elif choice == "0":
            print("\n👋 Saindo. Adeus, Master! Encerrando com qualidade.")
            break
        else:
            print("\n❌ Opção inválida. Tente novamente.\n")

if __name__ == "__main__":
    main()
