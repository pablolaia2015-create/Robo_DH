import streamlit as st
import os, glob, json, time
import contextlib
from io import StringIO
from src.scraper import start_extraction
from src.uploader import start_upload

st.set_page_config(page_title="DH ROBOT FINAL", page_icon="🦾", layout="wide")
st.title("🤖 DH ROBOT - V23.3 (Auto-Fix)")

os.makedirs("data", exist_ok=True)

def list_files_and_fix():
    # Pega TODOS os ficheiros na pasta data (mesmo os que não têm .json)
    arquivos = glob.glob("data/*")
    ficheiros_prontos = []
    
    for f in arquivos:
        if os.path.isfile(f):
            # Se o ficheiro não tiver .json, o robô conserta o nome sozinho!
            if not f.endswith('.json') and not f.endswith('.csv'):
                novo_nome = f + ".json"
                try:
                    os.rename(f, novo_nome)
                    ficheiros_prontos.append(novo_nome)
                except:
                    ficheiros_prontos.append(f)
            else:
                ficheiros_prontos.append(f)
                
    return ficheiros_prontos

# --- 1. EXTRAÇÃO ---
st.subheader("1️⃣ Passo: Extrair")
url_input = st.text_input("Cole o link COMPLETO aqui:", placeholder="https://www.diy.ie/...")

if st.button("🚀 INICIAR EXTRAÇÃO", use_container_width=True):
    if "http" in url_input:
        st.info("A extrair... Aguarde.")
        log_capture = StringIO()
        with contextlib.redirect_stdout(log_capture), contextlib.redirect_stderr(log_capture):
            try:
                start_extraction(url_input.strip())
            except Exception as e:
                print(f"Erro: {e}")
        
        # Só mostramos o log se der erro para não poluir o ecrã
        arquivos_agora = list_files_and_fix()
        if arquivos_agora:
            st.success("✅ Extração perfeita! Ficheiro guardado e corrigido.")
            time.sleep(1)
            st.rerun()
        else:
            st.error("❌ Erro. O robô não conseguiu criar o ficheiro.")
            st.text_area("Log de Erro:", log_capture.getvalue(), height=150)
    else:
        st.error("Link inválido.")

st.markdown("---")

# --- 2. REVISÃO ---
st.subheader("🔍 2️⃣ Passo: Revisar Dados Extraídos")
arquivos = list_files_and_fix()

if arquivos:
    selected_file = st.selectbox("Escolha um ficheiro para revisar:", arquivos)
    if selected_file:
        with st.expander(f"Ver conteúdo de: {os.path.basename(selected_file)}", expanded=True):
            try:
                with open(selected_file, 'r', encoding='utf-8') as f:
                    st.json(json.load(f))
            except Exception as e:
                st.warning(f"Não é um JSON válido. Lendo como texto: {e}")
                with open(selected_file, 'r', encoding='utf-8') as f:
                    st.text(f.read())
        
        if st.button("🗑️ Apagar este ficheiro (Se tiver erros)", use_container_width=True):
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
                st.success("✨ TUDO ENVIADO COM SUCESSO!")
                st.snow()
            except Exception as e:
                st.error(f"Erro no Upload: {e}")
    else:
        st.error("Nada para enviar!")
