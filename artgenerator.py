import streamlit as st
import requests
import time
from fpdf import FPDF  # <--- ERRORE RISOLTO: Mancava questa riga!

# --- LOGICA TESTUALE (Indipendente) ---
def genera_analisi_testuale(pittore, soggetto):
    api_url = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
    headers = {"Authorization": f"Bearer {st.secrets['HF_API_KEY']}"}
    prompt = f"<s>[INST] Scrivi una breve e colta analisi critica su '{soggetto}' nello stile pittorico di {pittore}. [/INST]"
    
    try:
        response = requests.post(api_url, headers=headers, json={"inputs": prompt, "parameters": {"max_new_tokens": 400}}, timeout=15)
        if response.status_code == 200:
            return response.json()[0]['generated_text'].split("[/INST]")[-1].strip()
        return f"Un'affascinante visione di {soggetto} interpretata con la maestria tipica di {pittore}."
    except:
        return f"Un'affascinante visione di {soggetto} interpretata con la maestria tipica di {pittore}."

# --- LOGICA IMMAGINE (Indipendente) ---
def genera_immagine_flux(pittore, soggetto):
    api_url = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell"
    headers = {"Authorization": f"Bearer {st.secrets['HF_API_KEY']}"}
    prompt = f"Oil painting of {soggetto} in the style of {pittore}."
    
    for _ in range(3):
        try:
            response = requests.post(api_url, headers=headers, json={"inputs": prompt}, timeout=20)
            if response.status_code == 200:
                return response.content
            time.sleep(5)
        except:
            continue
    return None

# --- UI (Layout a due colonne) ---
st.set_page_config(page_title="Il Pennello del Tempo", layout="wide")
st.title("🎨 Il Pennello del Tempo")
p_in = st.text_input("Artista")
s_in = st.text_input("Soggetto")

col1, col2 = st.columns(2)

# PULSANTE 1: ANALISI
if col1.button("Genera Analisi Testuale"):
    if p_in and s_in:
        with st.spinner("Il critico sta scrivendo..."):
            st.session_state.analisi = genera_analisi_testuale(p_in, s_in)
            st.session_state.pittore_pdf = p_in # Salvo per dare il nome al file scaricato
    else:
        st.warning("Inserisci Artista e Soggetto.")

# PULSANTE 2: IMMAGINE
if col2.button("Genera Visione Visiva"):
    if p_in and s_in:
        with st.spinner("Il pittore sta dipingendo..."):
            st.session_state.immagine = genera_immagine_flux(p_in, s_in)
    else:
        st.warning("Inserisci Artista e Soggetto.")

# --- VISUALIZZAZIONE ---
if st.session_state.get('analisi'):
    st.info(st.session_state.analisi)

if 'immagine' in st.session_state:
    if st.session_state.immagine:
        st.image(st.session_state.immagine, use_container_width=True)
    else:
        st.error("L'immagine non è stata generata per sovraccarico del server. Riprova.")

# --- GENERAZIONE PDF (Appare SOLO se entrambi sono pronti) ---
# ERRORE RISOLTO: Il codice ora usa le variabili corrette al posto di r["t"]
if st.session_state.get('analisi') and st.session_state.get('immagine'):
    st.divider() # Linea di separazione
    
    try:
        pdf = FPDF(unit='mm', format=(400, 280))
        pdf.add_page()
        pdf.set_font("Arial", size=14)
        
        # Inserimento Testo
        testo_pulito = st.session_state.analisi.encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 10, txt=testo_pulito)
        
        # Inserimento Immagine
        with open("tmp.jpg", "wb") as f: 
            f.write(st.session_state.immagine)
        
        pdf.add_page()
        pdf.image("tmp.jpg", x=20, y=20, w=360)
        
        # Tasto Download
        nome_file = st.session_state.get('pittore_pdf', 'Opera')
        st.download_button(
            label="💾 Scarica Dossier PDF Completo", 
            data=pdf.output(dest='S').encode('latin-1'), 
            file_name=f"{nome_file}.pdf"
        )
    except Exception as e:
        st.error(f"Impossibile generare il PDF: {e}")
