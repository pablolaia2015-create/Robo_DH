import streamlit as st
import os
import glob
from src.scraper import start_extraction
from src.uploader import start_upload

st.set_page_config(page_title="DH ROBOT V22.1", page_icon="🤖")
st.title("🤖 DH ROBOT - V22.1 (Smart Mode)")

# Garante que a pasta data existe no servidor
if not os.path.exists("data"):
    os.makedirs("data")

def get_pending_files():
    files = glob.glob("data/*.json") + glob.glob("data/*.csv")
    return [os.path.basename(f) for f in files]

# --- 1. SCRAPER ---
st.subheader("1️⃣ STEP 1: Scrape")
links_input = st.text_area("Paste links here:", height=100, placeholder="https://www.diy.ie/...")

if st.button("🚀 START EXTRACTION", use_container_width=True):
    if links_input.strip():
        # Limpa os links e garante que são URLs completas
        lines = links_input.split('\n')
        raw_links = []
        for l in lines:
            link = l.strip()
            if not link: continue
            # Se o link não tiver o domínio, o robô adiciona automaticamente!
            if "diy.ie" not in link:
                link = "https://www.diy.ie/departments/" + link
            raw_links.append(link)
        
        st.info(f"Checking {len(raw_links)} links...")
        
        for link in raw_links:
            try:
                with st.status(f"Extracting: {link[:40]}...", expanded=False):
                    start_extraction(link)
                st.success(f"✅ Extracted: {link.split('/')[-1][:20]}...")
            except Exception as e:
                st.error(f"❌ Error on {link[:30]}: {e}")
        st.rerun()
    else:
        st.error("Paste something first!")

st.markdown("---")
# --- 2. MONITOR ---
st.subheader("📦 Pending Files on Server")
pending = get_pending_files()
if pending:
    st.warning(f"Found {len(pending)} files ready:")
    for f in pending: st.write(f"📄 {f}")
else:
    st.info("No files ready. Paste a link above and click Start.")

st.markdown("---")
# --- 3. UPLOAD ---
st.subheader("2️⃣ STEP 2: Upload")
if st.button("📤 UPLOAD EVERYTHING", type="primary", use_container_width=True):
    if not pending:
        st.error("Nothing to upload!")
    else:
        with st.spinner("Uploading to Alvim Site..."):
            try:
                start_upload()
                st.success("✨ MISSION COMPLETE!")
                st.snow()
                st.rerun()
            except Exception as e:
                st.error(f"Upload failed: {e}")
