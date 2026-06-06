import os, sys, time, shutil, importlib, json
import cloudscraper
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# --- PATH CONFIGURATION (Memory folder) ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MEMORY_DIR = os.path.join(BASE_DIR, "memory")

# Ensure memory folder exists
os.makedirs(MEMORY_DIR, exist_ok=True)

sys.path.append(os.path.join(BASE_DIR, 'src'))

# Initial Import (Can be reloaded later)
import src.scraper as scraper
import src.uploader as uploader

# Define text file paths
LINKS_FILE = os.path.join(MEMORY_DIR, "processed_links.txt")
BATCH_FILE = os.path.join(MEMORY_DIR, "batch_links.txt")

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    clear_screen()
    print("\n" + "═"*50)
    print(" 🤖 DUBLINER HANDYMAN ROBOT - COMMAND PANEL")
    print(" 🌟 VERSION V28.5 SUPER PRO (GPS + API INTEGRATED)")
    print("═"*50 + "\n")

# --- TURBO CATEGORY VACUUM (STEALTH MODE) ---
def extract_category_links(category_url):
    print("\n⏳ Starting the 'Turbo Vacuum' (Stealth Mode)...")
    print("💡 It will open Chrome automatically to ensure all hidden products are loaded!")
    
    # Prepare Stealth Browser
    options = uc.ChromeOptions()
    options.add_argument("--window-size=1920,1080")
    # Note: Not using headless to prevent immediate Cloudflare blocks
    driver = uc.Chrome(options=options, version_main=148)
    
    try:
        driver.get(category_url)
        print("⏳ Giving 8 seconds for the site to load products and bypass security...")
        time.sleep(8)

        # Click cookies if they appear (helps unblock page layout)
        try:
            buttons = driver.find_elements(By.XPATH, "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'accept') or contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'aceitar')]")
            if buttons:
                buttons[0].click()
                time.sleep(2)
        except: pass

        # Automatic SCROLL to load lazy elements
        print("📜 Scrolling down to reveal all items (Please wait)...")
        last_height = driver.execute_script("return document.body.scrollHeight")
        for _ in range(6): # Tries to scroll 6 times
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2.5)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break # Reached the bottom of the page
            last_height = new_height

        # Now that everything is loaded, vacuum the HTML
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        found_links = set()

        # Search for all links on the loaded page
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            full_url = urljoin(category_url, href)
            
            # UNIVERSAL FILTER: Works for Obramat (and halfway there for other stores)
            if "/produtos/" in full_url and full_url.endswith(".html"):
                found_links.add(full_url)
            elif "/p/" in full_url: # Common pattern for other stores
                found_links.add(full_url)

        if found_links:
            with open(BATCH_FILE, "w", encoding="utf-8") as f:
                for link in found_links:
                    f.write(link + "\n")
            print(f"\n✅ ABSOLUTE SUCCESS! {len(found_links)} product links saved in 'batch_links.txt'.")
            print("💡 Tip: Now open the file, copy the links, and send them to Telegram or use Option 2!")
        else:
            print("\n⚠️ The page loaded and scrolled, but no links matching the product structure were found.")
            
    except Exception as e:
        print(f"\n❌ An error occurred in the Vacuum: {e}")
    finally:
        print("🚪 Closing Vacuum Chrome...")
        driver.quit()

# --- MAIN MENU ---
def main_menu():
    while True:
        print_header()
        print("✅ CHOOSE AN ACTION:")
        print("  [ 1 ] 🎯 SINGLE SCRAPE (Extract one Product)")
        print("  [ 2 ] 🚀 BATCH SCRAPE (Interactive Buffer)")
        print("  [ 3 ] 📤 UPLOAD TO WEBSITE (ALVIM)")
        print("  [ 4 ] 📂 VIEW LEARNED CATEGORIES")
        print("  [ 5 ] ☁️  CLOUD PUSH (Save to GitHub)")
        print("  [ 6 ] ☁️  CLOUD PULL (Download from GitHub)")
        print("  [ 7 ] 🗑️  DELETE LINK & FOLDER (Total Cleanup/Deep Scan)")
        print("  [ 8 ] 🔄 REFRESH (Reload Scraper Code)")
        print("  [ 9 ] 🧲 LINK VACUUM (Extract from a Category)")
        print("  [ 10] 🌐 START API SERVER (Listen to Telegram/Web Panel)")
        print("  [ 0 ] 👋 EXIT")
        print("-" * 50)

        choice = input("👉 Enter an option (0-10): ").strip()

        if choice == "1":
            print("\n" + "*"*40)
            print("🎯 SINGLE SCRAPER MODE ACTIVE")
            link = input("🔗 PASTE THE PRODUCT LINK: ").strip()
            if link:
                print("\n🕵️‍♂️ Initiating stealth extraction...")
                scraper.start_extraction(link)
            else:
                print("\n❌ Error: No link was pasted.")
            input("\n🔙 Press ENTER to return to menu...")

        elif choice == "2":
            print("\n" + "*"*40)
            print("🚀 BATCH SCRAPER MODE ACTIVE")
            print("🔗 Paste links one by one and press ENTER.")
            print("✅ When finished, type 'ok' or 'OK' and press ENTER to start!")
            print("-" * 40)
            
            pending_links = []
            
            while True:
                entry = input(f"[{len(pending_links)} ready links] 👉 ").strip()
                
                if entry.lower() == 'ok':
                    break
                elif not entry:
                    continue
                else:
                    pending_links.append(entry)
                    
            print("-" * 40)
            
            if pending_links:
                print(f"🚦 Starting extraction of {len(pending_links)} links...")
                for i, link in enumerate(pending_links, 1):
                    print(f"\n[{i}/{len(pending_links)}] Processing: {link}")
                    scraper.start_extraction(link)
                    time.sleep(2)
                print("\n✅ Batch completed!")
            else:
                print("⚠️ Action canceled or no links were pasted.")
                
            input("\n🔙 Press ENTER to return to menu...")

        elif choice == "3":
            print("\n" + "^"*40)
            print("📤 UPLOAD MODE ACTIVE")
            print("Starting upload of products in the 'data' folder to Alvim...")
            uploader.start_upload()
            input("\n🔙 Press ENTER to return to menu...")

        elif choice == '4':
            print("\n" + "📂"*20)
            try:
                categories = scraper.load_categories()
                print("\n📚 The robot already knows these categories:")
                for i, cat in enumerate(categories, 1):
                    print(f"  {i}. {cat}")
            except Exception as e:
                print(f"⚠️ Error loading categories: {e}")
            input("\n🔙 Press ENTER to return to menu...")

        elif choice == "5":
            print("\n" + "☁️"*15)
            print("Starting Backup to GitHub...")
            os.system("git add .")
            os.system('git commit -m "Auto-backup V28.5 via Robot Menu"')
            os.system("git push")
            print("✅ Backup successfully completed!")
            input("\n🔙 Press ENTER to return to menu...")

        elif choice == "6":
            print("\n" + "☁️"*15)
            print("Checking for updates on GitHub...")
            os.system("git pull")
            print("✅ Update completed!")
            input("\n🔙 Press ENTER to return to menu...")

        elif choice == "7":
            print("\n" + "🗑️"*20)
            print("DELETE LINK FROM MEMORY AND CLEAN FOLDER MODE")
            target_url = input("🔗 PASTE THE LINK TO DELETE (Or leave blank to ignore): ").strip()

            if target_url:
                # 1. REMOVE FROM MEMORY
                link_removed = False
                if os.path.exists(LINKS_FILE):
                    with open(LINKS_FILE, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                    
                    with open(LINKS_FILE, "w", encoding="utf-8") as f:
                        for line in lines:
                            # Smart cleanup to avoid space/slash errors
                            if target_url.replace("https://", "").replace("http://", "").strip('/') not in line.strip():
                                f.write(line)
                            else:
                                link_removed = True
                
                if link_removed:
                    print("✅ Link successfully removed from processed memory!")
                else:
                    print("⚠️ Link not found in history (but we'll search the folder anyway...).")

                # 2. DEEP SCAN: SEARCH AND DESTROY PHYSICAL FOLDER
                folder_removed = False
                data_folder = os.path.join(BASE_DIR, "data")
                if os.path.exists(data_folder):
                    for folder_name in os.listdir(data_folder):
                        folder_path = os.path.join(data_folder, folder_name)
                        if os.path.isdir(folder_path):
                            json_path = os.path.join(folder_path, "data.json")
                            if os.path.exists(json_path):
                                try:
                                    with open(json_path, "r", encoding="utf-8") as f:
                                        data = json.load(f)
                                    
                                    saved_link = ""
                                    if "storeEntries" in data and len(data["storeEntries"]) > 0:
                                        saved_link = data["storeEntries"][0].get("link", "")
                                    
                                    if target_url in saved_link or saved_link in target_url:
                                        shutil.rmtree(folder_path)
                                        print(f"✅ Physical folder destroyed: '{folder_name}'")
                                        folder_removed = True
                                        break
                                except Exception as e:
                                    pass

                if not folder_removed:
                    print("⚠️ No folder containing this link was found on disk.")
                
                print("-" * 50)

            # 3. TOTAL CLEANUP
            total_cleanup = input("⚠️ Do you want to delete ALL products in the 'data' folder and clear memory to start fresh? (y/n): ").strip().lower()
            if total_cleanup == 'y':
                confirmation = input("🚨 WARNING: This will delete EVERYTHING. Are you sure? (y/n): ").strip().lower()
                if confirmation == 'y':
                    data_folder = os.path.join(BASE_DIR, "data")
                    if os.path.exists(data_folder):
                        shutil.rmtree(data_folder)
                        os.makedirs(data_folder, exist_ok=True)
                        print("✅ 'data' folder successfully formatted!")
                    
                    if os.path.exists(LINKS_FILE):
                        os.remove(LINKS_FILE)
                        print("✅ Link history cleared!")
                else:
                    print("🛑 Total cleanup canceled.")
            else:
                print("🛑 Operation finished.")
                
            input("\n🔙 Press ENTER to return to menu...")
            
        elif choice == "8":
            print("\n🔄 Reloading Scraper and Uploader code...")
            try:
                importlib.reload(scraper)
                importlib.reload(uploader)
                print("✅ Systems successfully updated! Ready to run with new changes.")
            except Exception as e:
                print(f"❌ Error reloading files: {e}")
            input("\n🔙 Press ENTER to return to menu...")

        elif choice == "9":
            print("\n" + "🧲"*20)
            print("LINK VACUUM MODE ACTIVE")
            target_url = input("🔗 PASTE THE CATEGORY PAGE LINK: ").strip()
            if target_url:
                extract_category_links(target_url)
            else:
                print("❌ Invalid or empty link.")
            input("\n🔙 Press ENTER to return to menu...")

        elif choice == "10":
            print("\n" + "🌐"*20)
            print("Starting API Server...")
            print("⚠️ WARNING: The menu will be paused while the server listens to the Web.")
            print("🛑 To stop the server and return to this menu, press [ CTRL + C ]")
            print("-" * 50)
            try:
                # Calls the server script
                os.system("python api_server.py")
            except KeyboardInterrupt:
                pass # Catches Ctrl+C to avoid breaking the menu
            print("\n🛑 Server stopped. Returning to main menu...")
            time.sleep(1)

        elif choice == "0":
            print("\n👋 Shutting down engines. Goodbye, Master! Terminating with quality.")
            time.sleep(1)
            break
            
        else:
            print("\n❌ Invalid option. Try again.")
            time.sleep(1.5)

# --- START PROGRAM ---
if __name__ == "__main__":
    main_menu()