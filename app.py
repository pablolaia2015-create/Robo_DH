import streamlit as st
import os
import glob
import time
from src.scraper import start_extraction
from src.uploader import start_upload

st.set_page_config(page_title="DH ROBOT V22.2", page_icon="🤖")
st.title("🤖 DH ROBOT - V22.2 (Debug Mode)")

# Garante que a pasta data existe
if not os.path.exists("data"):
    os.makedirs("data")

def get_pending_files():
    files = glob.glob("data/*.json") + glob.glob("data/*.csv")
    return [os.path.basename(f) for f in files]

# --- 1. SCRAPER ---
st.subheader("1️⃣ STEP 1: Scrape")
links_input = st.text_area("Paste FULL links here (https://...):", height=100)

if st.button("🚀 START EXTRACTION", use_container_width=True):
    if links_input.strip():
        raw_links = [l.strip() for l in links_input.split('\n') if l.strip()]
        
        for link in raw_links:
            # Se o link for parcial, tentamos completar
            full_url = link if "http" in link else f"https://www.diy.ie/departments/{link}"
            
            st.info(f"Trying: {full_url[:50]}...")
            
            try:
                # Rodar a extração
                start_extraction(full_url)
                st.success(f"✅ Extracted successfully!")
                time.sleep(1) # Dá tempo para o arquivo ser gravado
            except Exception as e:
                st.error(f"❌ FAILED! Error: {e}")
        
        # Botão para atualizar a lista manualmente após extração
        if st.button("🔄 Refresh List"):
            st.rerun()
    else:
        st.error("Please paste a link first!")

st.markdown("---")

# --- 2. MONITOR ---
st.subheader("📦 Pending Files on Server")
pending = get_pending_files()
if pending:
    st.warning(f"Found {len(pending)} files ready:")
    for f in pending: st.write(f"📄 {f}")
else:
    st.info("No files found. If you just extracted, wait 2 seconds and click Refresh.")

st.markdown("---")

# --- 3. UPLOAD ---
st.subheader("2️⃣ STEP 2: Upload")
if st.button("📤 UPLOAD EVERYTHING", type="primary", use_container_width=True):
    if not pending:
        st.error("Nothing to upload!")
    else:
        with st.spinner("Uploading..."):
            try:
                start_upload()
                st.success("✨ UPLOAD COMPLETE!")
                st.snow()
            except Exception as e:
                st.error(f"Upload failed: {e}")

