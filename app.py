import streamlit as st
import os, json, time, shutil, glob
import contextlib
from io import StringIO
from src.scraper import start_extraction
from src.uploader import start_upload

st.set_page_config(page_title="DH ROBOT FINAL", page_icon="🦾", layout="wide")
st.title("🤖 DH ROBOT - V26.1 (HD Fix)")

os.makedirs("data", exist_ok=True)

def list_json_files():
    arquivos = []
    for root, dirs, files in os.walk("data"):
        for file in files:
            if file.endswith(".json"):
                arquivos.append(os.path.join(root, file))
    return arquivos

st.subheader("1️⃣ Passo: Extrair")
url_input = st.text_input("Cole o link COMPLETO aqui:", placeholder="https://www.diy.ie/...")

if st.button("🚀 INICIAR EXTRAÇÃO", use_container_width=True):
    if "http" in url_input:
        st.info("A forçar download das fotos originais... Aguarde.")
        log_capture = StringIO()
        with contextlib.redirect_stdout(log_capture), contextlib.redirect_stderr(log_capture):
            try:
                start_extraction(url_input.strip())
            except Exception as e:
                print(f"Erro: {e}")
        
        if list_json_files():
            st.success("✅ Extração perfeita!")
            time.sleep(2)
            st.rerun()
        else:
            st.error("❌ Ocorreu um erro.")
    else:
        st.error("Link inválido.")

st.markdown("---")

st.subheader("🔍 2️⃣ Passo: Revisar Dados e Imagens")
arquivos = list_json_files()

if arquivos:
    opcoes = {f: os.path.basename(os.path.dirname(f)) for f in arquivos}
    selected_file = st.selectbox("Escolha um produto para revisar:", arquivos, format_func=lambda x: opcoes[x])
    
    if selected_file:
        pasta_do_produto = os.path.dirname(selected_file)
        imagens = []
        for ext in ("*.jpg", "*.jpeg", "*.png", "*.webp"):
            imagens.extend(glob.glob(os.path.join(pasta_do_produto, ext)))
            
        with st.expander(f"Revisar: {opcoes[selected_file]}", expanded=True):
            aba1, aba2 = st.tabs(["📝 Dados (Texto)", f"🖼️ Imagens HD ({len(imagens)})"])
            
            with aba1:
                try:
                    with open(selected_file, 'r', encoding='utf-8') as f:
                        st.json(json.load(f))
                except Exception as e:
                    st.warning(f"Erro a ler os dados: {e}")
                    
            with aba2:
                if imagens:
                    st.info("💡 DICA: Clica no ícone das setinhas ⤢ no canto superior direito da imagem para ver em ecrã inteiro!")
                    cols = st.columns(2)
                    for i, img_path in enumerate(imagens):
                        # Imagem limpa e nativa. O botão de expandir já vem com ela!
                        cols[i % 2].image(img_path, use_container_width=True, caption=f"Foto {i+1}")
                else:
                    st.info("Nenhuma imagem encontrada nesta pasta.")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Apagar apenas este produto", use_container_width=True):
                shutil.rmtree(pasta_do_produto)
                st.rerun()
        with col2:
            if st.button("💣 LIMPAR BANCADA INTEIRA", type="primary", use_container_width=True):
                shutil.rmtree("data")
                os.makedirs("data", exist_ok=True)
                st.rerun()
else:
    st.info("Nenhum arquivo encontrado para revisão.")

st.markdown("---")

st.subheader("📤 3️⃣ Passo: Enviar para o Site")
if st.button("🚀 UPLOAD FINAL PARA O ALVIM", type="primary", use_container_width=True):
    if arquivos:
        with st.spinner("Enviando tudo para o servidor..."):
            try:
                start_upload()
                st.success("✨ TUDO ENVIADO COM SUCESSO!")
                st.balloons()
            except Exception as e:
                st.error(f"Erro no Upload: {e}")
    else:
        st.error("Nada para enviar!")
