import os, sys, time
# Adiciona src ao caminho para podermos importar os módulos
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))
from scraper import start_extraction
# from uploader import start_upload  # Desativado temporariamente

def print_header():
    print("\n" + "="*40)
    print("         DUBLINER HANDYMAN ROBOT")
    print("             VERSION V27.5 GOLD")
    print("="*40 + "\n")

def print_menu():
    print("✅ ESCOLHA UMA AÇÃO:")
    print("   [1] 🕷️ SCRAPE PRODUTO (B&Q)")
    print("   [2] 📤 UPLOAD PARA O SITE (ALVIM)")
    print("   [3] ☁️ CLOUD PUSH (Guardar no GitHub)")
    print("   [4] ☁️ CLOUD PULL (Baixar do GitHub)")
    print("   [0] 👋 SAIR")
    print("-" * 40)

def main():
    print_header()

    while True:
        print_menu()
        choice = input("👉 Digite uma opção: ").strip()

        if choice == "1":
            print("\n" + "*"*40)
            print("🕷️ MODO SCRAPER B&Q ATIVO")
            link = input("🔗 COLE O LINK DA B&Q: ").strip()
            if not link:
                print("\n❌ Erro: Nenhum link foi colado.")
                continue
            print("\n🕵️‍♂️ Iniciando extração furtiva...")
            start_extraction(link)
            print("*"*40 + "\n")

        elif choice == "2":
            print("\n" + "^"*40)
            print("📤 MODO UPLOAD ATIVO")
            print("Upload em pausa. Foco na extração local e Nuvem.")
            print("^"*40 + "\n")

        elif choice == "3":
            print("\n" + "☁️"*15)
            print("Iniciando Backup para o GitHub...")
            os.system("git add .")
            os.system('git commit -m "Auto-backup V27.5 pelo Menu do Robo"')
            os.system("git push")
            print("✅ Backup concluído com sucesso!")
            print("☁️"*15 + "\n")

        elif choice == "4":
            print("\n" + "☁️"*15)
            print("Procurando atualizações no GitHub...")
            os.system("git pull")
            print("✅ Atualização concluída!")
            print("☁️"*15 + "\n")

        elif choice == "0":
            print("\n👋 Saindo. Adeus, Master! Encerrando com qualidade.")
            break
        else:
            print("\n❌ Opção inválida. Tente novamente.\n")

if __name__ == "__main__":
    main()