import os
from src.scraper import start_extraction
from src.uploader import start_upload

def main():
    while True:
        print("\n" + "="*35)
        print("      🤖 DH ROBOT - V17.5 PRO")
        print("="*35)
        print("[1] SCRAPE (Extrair do B&Q)")
        print("[2] UPLOAD (Enviar para o Alvim)")
        print("[3] CLOUD PUSH (Guardar na Nuvem)")
        print("[4] CLOUD PULL (Baixar da Nuvem)")
        print("[0] SAIR")
        
        choice = input("\nEscolha: ")
        
        if choice == "1":
            url = input("Cole o link do produto: ")
            if url.strip():
                start_extraction(url)
            else:
                print("❌ Erro: O link não pode estar vazio!")
                
        elif choice == "2":
            # Aqui o robô tenta o upload (esperando a chave do Alvim)
            start_upload()
            
        elif choice == "3":
            print("\n☁️ A subir alterações para o GitHub...")
            os.system("git add .")
            # Aspas duplas para o Windows não se perder nos espaços
            os.system('git commit -m "Auto-sync from Robot Menu"')
            os.system("git push origin main")
            print("✅ Tudo guardado na nuvem!")

        elif choice == "4":
            print("\n📥 A baixar novidades do GitHub...")
            # Puxa o que foi feito no telemóvel para o notebook
            os.system("git pull origin main")
            print("✅ Notebook atualizado com sucesso!")
            
        elif choice == "0":
            print("Goodbye, Pablo! Bom descanso.")
            break
            
        else:
            print("Opção Inválida!")

if __name__ == "__main__":
    main()