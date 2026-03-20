import os
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("URL_PRODUTOS")
key = os.getenv("ADMIN_API_SECRET")

print("\n--- CHECKING CONNECTION TO .ENV ---")
print(f"Target URL: {url}")

if key:
    # Mostra apenas o início e o fim da chave por segurança
    masked_key = f"{key[:3]}***{key[-3:]}"
    print(f"API Key found: {masked_key} (Length: {len(key)})")
else:
    print("❌ API Key NOT FOUND! Check your .env file name and location.")
print("-----------------------------------\n")