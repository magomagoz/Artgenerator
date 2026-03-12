import streamlit as st
from fpdf import FPDF
import os
import requests
import time

# --- Configurazione API (Usa secrets.toml) ---
HF_API_KEY = st.secrets["HF_API_KEY"]
STABILITY_API_KEY = st.secrets["STABILITY_API_KEY"]

def genera_analisi_robusta(pittore, soggetto):
    """Analisi testuale strutturata e lunga."""
    prompt = (f"Scrivi una recensione d'arte profonda di 600 parole su come {pittore} dipingerebbe '{soggetto}'. "
              "Struttura in 3 capitoli: Analisi Tecnica, Composizione, Interpretazione Concettuale. "
              "Usa un tono colto, ricercato e discorsivo.")
    
    # Tentativo Mistral
    try:
        api_url = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
        payload = {"inputs": f"<s>[INST] {prompt} [/INST]", "parameters": {"max_new_tokens": 1000}}
        response = requests.post(api_url, headers={"Authorization": f"Bearer {HF_API_KEY}"}, json=payload)
        if response.status_code == 200:
            return response.json()[0]['generated_text'].split("[/INST]")[-1].strip()
    except:
        return f"Interpretazione magistrale di {soggetto} nello stile di {pittore}."

# 1. Definizione della funzione (deve essere definita PRIMA di essere usata)
def genera_immagine_gratis(pittore, soggetto):
    api_url = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell"
    headers = {"Authorization": f"Bearer {st.secrets['HF_API_KEY']}"}
    prompt = f"Oil painting of {soggetto} in the style of {pittore}."
    
    for i in range(3):
        response = requests.post(api_url, headers=headers, json={"inputs": prompt})
        if response.status_code == 200:
            return response.content
        time.sleep(5) # Attesa tra i tentativi
    return None


# --- UI e Logica ---
st.set_page_config(page_title="Il Pennello del Tempo", layout="wide")
st.title("🎨 Il Pennello del Tempo - Edizione Professionale")

if 'res' not in st.session_state: st.session_state.res = None

col1, col2 = st.columns(2)
p_in = col1.text_input("Artista")
s_in = col2.text_input("Soggetto")

# 2. Pulsante nel corpo principale
if st.button("Genera Visione Artistica"):
    with st.spinner("Creazione in corso..."):
        # Ora la funzione è definita e il modulo 'time' è importato
        img = genera_immagine_gratis(p_in, s_in)
        if img:
            st.image(img)
        else:
            st.error("Errore: Server occupato. Riprova.")

if st.session_state.res:
    r = st.session_state.res
    st.info(r["t"])
    st.image(r["i"], use_container_width=True)
    
    # Download PDF
    pdf = FPDF(unit='mm', format=(400, 280))
    pdf.add_page()
    pdf.set_font("Arial", size=14)
    pdf.multi_cell(0, 10, txt=r["t"].encode('latin-1', 'replace').decode('latin-1'))
    
    # Salva e scarica
    with open("tmp.jpg", "wb") as f: f.write(r["i"])
    pdf.add_page()
    pdf.image("tmp.jpg", x=20, y=20, w=360)
    st.download_button("💾 Scarica Dossier PDF", data=pdf.output(dest='S').encode('latin-1'), file_name="opera.pdf")
