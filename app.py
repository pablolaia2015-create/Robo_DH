import streamlit as st
import os, json, time, shutil
import contextlib
from io import StringIO
from src.scraper import start_extraction
from src.uploader import start_upload

st.set_page_config(page_title="DH ROBOT V24", page_icon="🦾", layout="wide")
st.title("🤖 DH ROBOT - V24.0 (Folder Fix)")

os.makedirs("data", exist_ok=True)

def list_json_files():
    # O robô agora "entra" em todas as subpastas para procurar os ficheiros de dados
    arquivos = []
    for root, dirs, files in os.walk("data"):
        for file in files:
            if file.endswith(".json"):
                arquivos.append(os.path.join(root, file))
    return arquivos

# --- 1. EXTRAÇÃO ---
st.subheader("1️⃣ Passo: Extrair")
url_input = st.text_input("Cole o link COMPLETO aqui:", placeholder="https://www.diy.ie/...")

if st.button("🚀 INICIAR EXTRAÇÃO", use_container_width=True):
    if "http" in url_input:
        st.info("A extrair e a criar as pastas... Aguarde.")
        log_capture = StringIO()
        with contextlib.redirect_stdout(log_capture), contextlib.redirect_stderr(log_capture):
            try:
                start_extraction(url_input.strip())
            except Exception as e:
                print(f"Erro: {e}")
        
        arquivos_agora = list_json_files()
        if arquivos_agora:
            st.success("✅ Extração perfeita! Dados encontrados nas pastas.")
            time.sleep(2)
            st.rerun()
        else:
            st.error("❌ O robô criou a pasta, mas não encontrou o ficheiro JSON lá dentro.")
            st.text_area("Log de Erro:", log_capture.getvalue(), height=150)
    else:
        st.error("Link inválido.")

st.markdown("---")

# --- 2. REVISÃO ---
st.subheader("🔍 2️⃣ Passo: Revisar Dados Extraídos")
arquivos = list_json_files()

if arquivos:
    # Mostra o nome da pasta (produto) para ser mais fácil de ler
    opcoes = {f: os.path.basename(os.path.dirname(f)) for f in arquivos}
    selected_file = st.selectbox("Escolha um produto para revisar:", arquivos, format_func=lambda x: opcoes[x])
    
    if selected_file:
        with st.expander(f"Ver os adesivos de: {opcoes[selected_file]}", expanded=True):
            try:
                with open(selected_file, 'r', encoding='utf-8') as f:
                    st.json(json.load(f))
            except Exception as e:
                st.warning(f"Erro a ler os dados: {e}")
        
        if st.button("🗑️ Apagar este produto (Se tiver erros)", use_container_width=True):
            pasta_do_produto = os.path.dirname(selected_file)
            shutil.rmtree(pasta_do_produto) # Apaga a pasta inteira (fotos e json)
            st.rerun()
else:
    st.info("Nenhum arquivo encontrado para revisão.")

st.markdown("---")

# --- 3. UPLOAD ---
st.subheader("📤 3️⃣ Passo: Enviar para o Site")
if st.button("🚀 UPLOAD FINAL PARA O ALVIM", type="primary", use_container_width=True):
    if arquivos:
        with st.spinner("Enviando tudo para o servidor do Alvim..."):
            try:
                start_upload()
                st.success("✨ TUDO ENVIADO COM SUCESSO!")
                st.snow()
            except Exception as e:
                st.error(f"Erro no Upload: {e}")
    else:
        st.error("Nada para enviar!")
