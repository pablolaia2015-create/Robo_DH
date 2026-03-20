import streamlit as st
import os, glob, json, time
from src.scraper import start_extraction
from src.uploader import start_upload

st.set_page_config(page_title="DH ROBOT REVIEWER", page_icon="📝", layout="wide")
st.title("🤖 DH ROBOT - V23.1 (Review Edition)")

# Garante que a pasta existe com permissão
DATA_DIR = "data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

def list_files():
    # Procura por qualquer ficheiro na pasta data
    return glob.glob(os.path.join(DATA_DIR, "*.*"))

# --- 1. EXTRAÇÃO ---
st.subheader("1️⃣ Passo: Extrair")
url_input = st.text_input("Cole o link COMPLETO aqui:", placeholder="https://www.diy.ie/...")

if st.button("🚀 INICIAR EXTRAÇÃO", use_container_width=True):
    if "http" in url_input:
        with st.spinner("Extraindo dados..."):
            try:
                start_extraction(url_input.strip())
                st.success("✅ Extração concluída!")
                time.sleep(2)
                st.rerun()
            except Exception as e:
                st.error(f"Erro na extração: {e}")
    else:
        st.error("Link inválido. Use o link completo do navegador.")

st.markdown("---")

# --- 2. REVISÃO DE DADOS (O que pediste!) ---
st.subheader("🔍 2️⃣ Passo: Revisar Dados Extraídos")
arquivos = list_files()

if arquivos:
    selected_file = st.selectbox("Escolha um ficheiro para revisar:", arquivos)
    
    if selected_file:
        with st.expander(f"Ver conteúdo de: {os.path.basename(selected_file)}", expanded=True):
            try:
                with open(selected_file, 'r', encoding='utf-8') as f:
                    conteudo = json.load(f)
                    st.json(conteudo) # Mostra os dados organizados
            except:
                st.warning("Não foi possível ler o ficheiro como JSON. Verificando texto plano...")
                with open(selected_file, 'r', encoding='utf-8') as f:
                    st.text(f.read())
        
        if st.button("🗑️ Apagar este ficheiro (Se estiver errado)", use_container_width=True):
            os.remove(selected_file)
            st.rerun()
else:
    st.info("Nenhum arquivo encontrado para revisão.")

st.markdown("---")

# --- 3. UPLOAD ---
st.subheader("📤 3️⃣ Passo: Enviar para o Site")
if st.button("🚀 UPLOAD FINAL PARA O ALVIM", type="primary", use_container_width=True):
    if arquivos:
        with st.spinner("Enviando para o servidor..."):
            try:
                start_upload()
                st.success("✨ TUDO ENVIADO E ARQUIVADO!")
                st.snow()
                time.sleep(2)
                st.rerun()
            except Exception as e:
                st.error(f"Erro no Upload: {e}")
    else:
        st.error("Não há ficheiros revisados para enviar!")
