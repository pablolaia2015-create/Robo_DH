import streamlit as st
import os
from src.scraper import start_extraction
from src.uploader import start_upload

st.set_page_config(page_title="DH ROBOT PRO", page_icon="🤖")
st.title("🤖 DH ROBOT - V18.5 WEB")

LOG_FILE = "processed_links.txt"

def get_processed_links():
    if not os.path.exists(LOG_FILE): return set()
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f if line.strip())

def save_link(url):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(url + "\n")

st.subheader("🚀 Turbo Scraper")
links_input = st.text_area("Paste links here (one per line):", height=200)

if st.button("🔥 START EXTRACTION"):
    if links_input.strip():
        processed_links = get_processed_links()
        raw_links = [l.strip() for l in links_input.split('\n') if "http" in l]
        unique_batch = list(dict.fromkeys(raw_links))
        
        st.info(f"Detected {len(unique_batch)} links.")
        for i, link in enumerate(unique_batch):
            if link in processed_links:
                st.warning(f"Skipped: {link[:50]}...")
            else:
                try:
                    start_extraction(link)
                    save_link(link)
                    st.success(f"Success: {link[:30]}...")
                except Exception as e:
                    st.error(f"Error: {e}")
        st.balloons()
    else:
        st.error("Paste at least one link!")
