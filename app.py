import streamlit as st
import os, json, shutil, glob
import contextlib
from io import StringIO

# --- MÁGICA DE SEGURANÇA ---
try:
    if "GOOGLE_API_KEY" in st.secrets:
        os.environ["GOOGLE_API_KEY"] = st.secrets["GOOGLE_API_KEY"]
except Exception:
    pass
# ---------------------------

from src.scraper import start_extraction
from src.uploader import start_upload

st.set_page_config(page_title="DH ROBOT FINAL", page_icon="🦾", layout="wide")
st.title("🤖 DH ROBOT - V26.3 (AI Diagnostic Mode)")

os.makedirs("data", exist_ok=True)

def list_json_files():
    files = []
    for root, dirs, filenames in os.walk("data"):
        for file in filenames:
            if file.endswith(".json"):
                files.append(os.path.join(root, file))
    return files

st.subheader("1️⃣ Step: Extract (Batch Mode)")
urls_input = st.text_area("Paste ALL FULL links here (one per line):", placeholder="https://www.diy.ie/...", height=150)

if st.button("🚀 START BATCH EXTRACTION", use_container_width=True):
    url_list = [url.strip() for url in urls_input.split('\n') if url.strip()]
    
    if url_list:
        st.info(f"Processing {len(url_list)} links... Please wait.")
        log_capture = StringIO()
        progress_bar = st.progress(0)
        
        with contextlib.redirect_stdout(log_capture), contextlib.redirect_stderr(log_capture):
            for index, url in enumerate(url_list):
                if "http" in url:
                    try:
                        start_extraction(url)
                    except Exception as e:
                        print(f"Error on {url}: {e}")
                progress_bar.progress((index + 1) / len(url_list))
                
        if log_capture.getvalue():
            with st.expander("🛠️ Ver Terminal do Robô (Logs)", expanded=True):
                st.text(log_capture.getvalue())
                
        if list_json_files():
            st.success("✅ Batch Extraction Completed!")
        else:
            st.error("❌ An error occurred or no new data was extracted.")
    else:
        st.warning("Please paste at least one valid link.")

st.markdown("---")

st.subheader("🔍 2️⃣ Step: Review Data and Images")
extracted_files = list_json_files()

if extracted_files:
    options = {f: os.path.basename(os.path.dirname(f)) for f in extracted_files}
    selected_file = st.selectbox("Choose a product to review:", extracted_files, format_func=lambda x: options[x])

    if selected_file:
        product_folder = os.path.dirname(selected_file)
        images = []
        for ext in ("*.jpg", "*.jpeg", "*.png", "*.webp"):
            images.extend(glob.glob(os.path.join(product_folder, ext)))

        with st.expander(f"Reviewing: {options[selected_file]}", expanded=True):
            tab1, tab2 = st.tabs(["📝 Data (Text)", f"🖼️ HD Images ({len(images)})"])

            with tab1:
                try:
                    with open(selected_file, 'r', encoding='utf-8') as f:
                        st.json(json.load(f))
                except Exception as e:
                    st.warning(f"Error reading data: {e}")

            with tab2:
                if images:
                    cols = st.columns(2)
                    for i, img_path in enumerate(images):
                        cols[i % 2].image(img_path, use_container_width=True, caption=f"Image {i+1}")
                else:
                    st.info("No images found in this folder.")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Delete ONLY this product", use_container_width=True):
                shutil.rmtree(product_folder)
                st.rerun()
        with col2:
            if st.button("💣 CLEAR ENTIRE WORKBENCH", type="primary", use_container_width=True):
                shutil.rmtree("data")
                os.makedirs("data", exist_ok=True)
                st.rerun()
else:
    st.info("No files found for review.")

st.markdown("---")
st.subheader("📤 3️⃣ Step: Upload to Website")
if st.button("🚀 FINAL UPLOAD TO ALVIM", type="primary", use_container_width=True):
    st.info("Conectando ao servidor do Alvim... Por favor, aguarde.")
    log_capture = StringIO()
    
    with contextlib.redirect_stdout(log_capture), contextlib.redirect_stderr(log_capture):
        start_upload()
        
    # Mostra o resultado do envio na tela!
    st.text(log_capture.getvalue())
    
    if "✅ SUCESSO" in log_capture.getvalue():
        st.success("🎉 Produto(s) enviado(s) para o banco de dados do Alvim com sucesso!")
        st.balloons()
