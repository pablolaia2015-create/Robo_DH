import os, sys, time

# Adiciona src ao caminho para podermos importar os módulos
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(BASE_DIR, 'src'))

from scraper import start_extraction
from uploader import start_upload  

# Define o caminho do ficheiro de memória para podermos apagá-lo por aqui
LINKS_FILE = os.path.join(BASE_DIR, "processed_links.txt")

def print_header():
    print("\n" + "="*40)
    print("        DUBLINER HANDYMAN ROBOT")
    print("            VERSION V27.7 PRO")
    print("="*40 + "\n")

def print_menu():
    print("✅ ESCOLHA UMA AÇÃO:")
    print("   [1] 🕷️ SCRAPE PRODUTO (Multi-Loja)")
    print("   [2] 📤 UPLOAD PARA O SITE (ALVIM)")
    print("   [3] ☁️ CLOUD PUSH (Guardar no GitHub)")
    print("   [4] ☁️ CLOUD PULL (Baixar do GitHub)")
    print("   [5] 🗑️ APAGAR LINK DA MEMÓRIA")
    print("   [0] 👋 SAIR")
    print("-" * 40)

def main():
    print_header()

    while True:
        print_menu()
        choice = input("👉 Digite uma opção: ").strip()

        if choice == "1":
            print("\n" + "*"*40)
            print("🕷️ MODO SCRAPER ATIVO")
            link = input("🔗 COLE O LINK DO PRODUTO: ").strip()
            if not link:
                print("\n❌ Erro: Nenhum link foi colado.")
                continue
            print("\n🕵️‍♂️ Iniciando extração furtiva...")
            start_extraction(link)
            print("*"*40 + "\n")

        elif choice == "2":
            print("\n" + "^"*40)
            print("📤 MODO UPLOAD ATIVO")
            print("Iniciando envio dos produtos na pasta 'data' para o Alvim...")
            start_upload()
            print("^"*40 + "\n")

        elif choice == "3":
            print("\n" + "☁️"*15)
            print("Iniciando Backup para o GitHub...")
            os.system("git add .")
            os.system('git commit -m "Auto-backup V27.7 pelo Menu do Robo"')
            os.system("git push")
            print("✅ Backup concluído com sucesso!")
            print("☁️"*15 + "\n")

        elif choice == "4":
            print("\n" + "☁️"*15)
            print("Procurando atualizações no GitHub...")
            os.system("git pull")
            print("✅ Atualização concluída!")
            print("☁️"*15 + "\n")

        elif choice == "5":
            print("\n" + "🗑️"*20)
            print("MODO APAGAR LINK DA MEMÓRIA")
            link_to_delete = input("🔗 COLE O LINK QUE DESEJA APAGAR: ").strip()
            if not link_to_delete:
                print("❌ Nenhum link colado.")
                continue
            
            if os.path.exists(LINKS_FILE):
                with open(LINKS_FILE, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                
                with open(LINKS_FILE, "w", encoding="utf-8") as f:
                    apagado = False
                    for line in lines:
                        # Compara ignorando espaços e quebras de linha
                        if line.strip() == link_to_delete:
                            apagado = True
                        else:
                            f.write(line)
                
                if apagado:
                    print("✅ Link apagado com sucesso! O robô já se esqueceu dele.")
                else:
                    print("⚠️ O link não foi encontrado na memória.")
            else:
                print("⚠️ O arquivo de memória ainda não existe.")
            print("🗑️"*20 + "\n")

        elif choice == "0":
            print("\n👋 Saindo. Adeus, Master! Encerrando com qualidade.")
            break
        else:
            print("\n❌ Opção inválida. Tente novamente.\n")

if __name__ == "__main__":
    main()