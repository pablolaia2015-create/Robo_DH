import streamlit as st
import os, glob, time
from src.scraper import start_extraction
from src.uploader import start_upload

st.set_page_config(page_title="DH ROBOT V23", page_icon="🦾")
st.title("🤖 DH ROBOT - V23.0")

# Cria a pasta data se não existir
if not os.path.exists("data"):
    os.makedirs("data")

# --- FUNÇÃO PARA LISTAR ARQUIVOS ---
def list_files():
    return glob.glob("data/*.json") + glob.glob("data/*.csv")

# --- 1. SCRAPER ---
st.subheader("1️⃣ Passo: Extrair")
url_input = st.text_input("Cole o link COMPLETO aqui:")

if st.button("🚀 INICIAR EXTRAÇÃO", use_container_width=True):
    if "http" in url_input:
        with st.spinner("Trabalhando..."):
            try:
                start_extraction(url_input.strip())
                st.success("✅ Extração concluída!")
                time.sleep(2)
                st.rerun()
            except Exception as e:
                st.error(f"Erro: {e}")
    else:
        st.error("Por favor, cole o link começando com https://")

st.markdown("---")

# --- 2. MONITOR ---
st.subheader("📦 Arquivos prontos para o Alvim")
arquivos = list_files()

if arquivos:
    st.warning(f"Temos {len(arquivos)} arquivos na fila:")
    for a in arquivos:
        st.write(f"📄 {os.path.basename(a)}")
else:
    st.info("Nenhum arquivo encontrado na pasta 'data'.")

st.markdown("---")

# --- 3. UPLOAD ---
st.subheader("2️⃣ Passo: Enviar para o Site")
if st.button("📤 ENVIAR AGORA", type="primary", use_container_width=True):
    if arquivos:
        with st.spinner("Enviando..."):
            try:
                start_upload()
                st.success("✨ TUDO ENVIADO COM SUCESSO!")
                st.snow()
                time.sleep(3)
                st.rerun()
            except Exception as e:
                st.error(f"Erro no Upload: {e}")
    else:
        st.error("Nada para enviar!")
