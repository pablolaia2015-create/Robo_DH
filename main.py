import os
from src.scraper import start_extraction
from src.uploader import start_upload

def main():
    while True:
        print("\n" + "="*30)
        print("      🤖 DH ROBOT - V17.5")
        print("="*30)
        print("[1] SCRAPE (Extract Product)")
        print("[2] UPLOAD (Send to Site)")
        print("[3] CLOUD  (Push to GitHub)")
        print("[0] EXIT")
        
        choice = input("\nChoose: ")
        
        if choice == "1":
            url = input("Paste URL: ")
            start_extraction(url)
        elif choice == "2":
            start_upload()
        elif choice == "3":
            print("☁️ Syncing with GitHub...")
            os.system("git add . && git commit -m 'Auto-sync from Robot Menu' && git push")
        elif choice == "0":
            print("Goodbye, Pablo!")
            break
        else:
            print("Invalid Option!")

if __name__ == "__main__":
    main()

