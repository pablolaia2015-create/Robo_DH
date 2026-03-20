import streamlit as st
import os, glob, json, time
import contextlib
from io import StringIO
from src.scraper import start_extraction
from src.uploader import start_upload

st.set_page_config(page_title="DH DETETIVE", page_icon="🕵️", layout="wide")
st.title("🤖 DH ROBOT - V23.2 (Detetive Mode)")

os.makedirs("data", exist_ok=True)

def list_files():
    # Procura na pasta data E na pasta principal para ver se ele se perdeu
    arquivos = glob.glob("data/*.*") + glob.glob("*.json") + glob.glob("*.csv")
    return list(set(arquivos)) # Remove duplicados

# --- 1. EXTRAÇÃO ---
st.subheader("1️⃣ Passo: Extrair")
url_input = st.text_input("Cole o link COMPLETO aqui:", placeholder="https://www.diy.ie/...")

if st.button("🚀 INICIAR EXTRAÇÃO", use_container_width=True):
    if "http" in url_input:
        st.info("A extrair... Aguarde.")
        
        # Vamos capturar TUDO o que o scraper diz escondido!
        log_capture = StringIO()
        with contextlib.redirect_stdout(log_capture), contextlib.redirect_stderr(log_capture):
            try:
                start_extraction(url_input.strip())
            except Exception as e:
                print(f"Erro Fatal no Scraper: {e}")
        
        log_text = log_capture.getvalue()
        
        # Mostra o log para nós lermos o que falhou
        if log_text.strip():
            st.text_area("🕵️ O que o Robô disse nos bastidores (LOG):", log_text, height=150)
        
        arquivos_agora = list_files()
        if arquivos_agora:
            st.success("✅ Extração concluiu E gerou o ficheiro!")
        else:
            st.error("❌ O robô tentou, mas NÃO conseguiu criar o ficheiro. Lê o Log acima!")
    else:
        st.error("Link inválido.")

st.markdown("---")

# --- 2. REVISÃO ---
st.subheader("🔍 2️⃣ Passo: Revisar Dados Extraídos")
arquivos = list_files()

if arquivos:
    selected_file = st.selectbox("Escolha um ficheiro para revisar:", arquivos)
    if selected_file:
        with st.expander(f"Ver conteúdo de: {os.path.basename(selected_file)}", expanded=True):
            try:
                with open(selected_file, 'r', encoding='utf-8') as f:
                    st.json(json.load(f))
            except:
                with open(selected_file, 'r', encoding='utf-8') as f:
                    st.text(f.read())
        
        if st.button("🗑️ Apagar este ficheiro"):
            os.remove(selected_file)
            st.rerun()
else:
    st.info("Nenhum arquivo encontrado para revisão.")

st.markdown("---")

# --- 3. UPLOAD ---
st.subheader("📤 3️⃣ Passo: Enviar para o Site")
if st.button("🚀 UPLOAD FINAL PARA O ALVIM", type="primary", use_container_width=True):
    if arquivos:
        with st.spinner("Enviando..."):
            try:
                start_upload()
                st.success("✨ ENVIADO!")
                st.snow()
            except Exception as e:
                st.error(f"Erro no Upload: {e}")
    else:
        st.error("Nada para enviar!")
