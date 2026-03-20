import streamlit as st
import os
from src.scraper import start_extraction
from src.uploader import start_upload

# --- App Configuration ---
st.set_page_config(page_title="DH ROBOT CORE", page_icon="🦾")

st.title("🤖 DH ROBOT - V21.0 CORE")
st.markdown("---")

# --- Memory Logic (Duplicate Check) ---
LOG_FILE = "processed_links.txt"

def get_processed_links():
    if not os.path.exists(LOG_FILE): return set()
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f if line.strip())

def save_link(url):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(url + "\n")

# --- SECTION 1: SCRAPER ---
st.subheader("1️⃣ STEP 1: Scrape Products")
links_input = st.text_area("Paste your DIY.ie links here:", height=150, placeholder="Example:\nhttps://www.diy.ie/...\nhttps://www.diy.ie/...")

if st.button("🚀 START EXTRACTION", use_container_width=True):
    if links_input.strip():
        processed_links = get_processed_links()
        raw_links = [l.strip() for l in links_input.split('\n') if "http" in l]
        unique_batch = list(dict.fromkeys(raw_links))
        
        st.info(f"Processing {len(unique_batch)} items...")
        
        for i, link in enumerate(unique_batch):
            if link in processed_links:
                st.warning(f"⏩ Skipped: {link[:45]}... (Already in database)")
            else:
                try:
                    start_extraction(link)
                    save_link(link)
                    st.success(f"✅ Extracted: {link[:35]}...")
                except Exception as e:
                    st.error(f"❌ Scrape Error: {e}")
        st.balloons()
    else:
        st.error("Please paste at least one link!")

st.markdown("---")

# --- SECTION 2: UPLOADER ---
st.subheader("2️⃣ STEP 2: Send to Alvim Site")
st.write("This will upload all extracted files and archive them.")

if st.button("📤 UPLOAD & ARCHIVE", type="primary", use_container_width=True):
    with st.spinner("Uploading products... Please wait."):
        try:
            start_upload()
            st.success("✨ MISSION COMPLETE! ALL PRODUCTS ARE LIVE!")
            st.snow()
        except Exception as e:
            st.error(f"❌ Upload Error: {e}")

st.markdown("---")
st.caption("Simplified Engine for High Productivity 🦾")
