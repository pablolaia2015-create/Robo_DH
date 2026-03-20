import os
from src.scraper import start_extraction
from src.uploader import start_upload

def main():
    while True:
        print("\n" + "="*30)
        print("    🤖 DH ROBOT - V17.5")
        print("="*30)
        print("[1] SCRAPE (Extract Product)")
        print("[2] UPLOAD (Send to Site)")
        print("[3] CLOUD  (Push to GitHub)")
        print("[0] EXIT")
        
        choice = input("\nChoose: ")
        
        if choice == "1":
            url = input("Paste URL: ")
            if url.strip():
                start_extraction(url)
            else:
                print("❌ Please paste a valid URL!")
                
        elif choice == "2":
            start_upload()
            
        elif choice == "3":
            print("\n☁️ Syncing with GitHub...")
            # Corrigido para Windows: usamos aspas duplas na mensagem do commit
            # E garantimos que ele tenta dar o push para a main
            os.system("git add .")
            os.system('git commit -m "Auto-sync from Robot Menu"')
            os.system("git push origin main")
            print("✅ Cloud Sync Complete!")
            
        elif choice == "0":
            print("Goodbye, Pablo!")
            break
            
        else:
            print("Invalid Option!")

if __name__ == "__main__":
    main()