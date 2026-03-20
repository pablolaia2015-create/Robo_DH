import streamlit as st
import os
import glob
from src.scraper import start_extraction
from src.uploader import start_upload

st.set_page_config(page_title="DH ROBOT DIAGNOSTIC", page_icon="🔍")
st.title("🤖 DH ROBOT - V22.0 (Diagnostic Mode)")

# --- Funções de Apoio ---
def get_pending_files():
    # Procura ficheiros .json ou .csv na pasta data do servidor
    files = glob.glob("data/*.json") + glob.glob("data/*.csv")
    return [os.path.basename(f) for f in files]

# --- 1. SCRAPER ---
st.subheader("1️⃣ STEP 1: Scrape")
links_input = st.text_area("Paste links here:", height=100)

if st.button("🚀 START EXTRACTION"):
    if links_input.strip():
        raw_links = [l.strip() for l in links_input.split('\n') if "http" in l]
        for link in raw_links:
            try:
                start_extraction(link)
                st.success(f"Done: {link[:30]}...")
            except Exception as e:
                st.error(f"Error: {e}")
        st.rerun() # Atualiza a página para mostrar os ficheiros novos

st.markdown("---")

# --- 2. MONITOR DE FICHEIROS (O que o Alvim vai receber) ---
st.subheader("📦 Pending Files on Server")
pending = get_pending_files()

if pending:
    st.warning(f"Found {len(pending)} files ready to upload:")
    for f in pending:
        st.write(f"📄 {f}")
else:
    st.info("No files found in 'data/' folder. Scrape something first!")

st.markdown("---")

# --- 3. UPLOAD ---
st.subheader("2️⃣ STEP 2: Upload")
if st.button("📤 UPLOAD EVERYTHING", type="primary"):
    if not pending:
        st.error("Nothing to upload!")
    else:
        with st.spinner("Uploading..."):
            try:
                # Aqui vamos ver o que o start_upload devolve
                start_upload()
                st.success("✨ MISSION COMPLETE!")
                st.snow()
                st.rerun()
            except Exception as e:
                st.error(f"Upload failed: {e}")
