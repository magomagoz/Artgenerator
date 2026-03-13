import streamlit as st
import requests
import time
from fpdf import FPDF  # <--- ERRORE RISOLTO: Mancava questa riga!
import urllib.parse # Aggiungi questo import in alto!
import io

# 1. Modifica la funzione Gemini (Il modello 2.5 non esiste!)
def genera_immagine_flux(pittore, soggetto):
    prompt = f"Oil painting of {soggetto} by {pittore}"
    prompt_url = urllib.parse.quote(prompt)
    # Restituiamo direttamente l'URL, non i byte!
    return f"https://image.pollinations.ai/prompt/{prompt_url}?width=1024&height=768&nologo=true&seed=42"

def genera_immagine_flux(pittore, soggetto):
    # Prompt più semplice per evitare errori
    prompt = f"Oil painting of {soggetto} by {pittore}"
    # Codifica URL corretta
    prompt_url = urllib.parse.quote(prompt)
    api_url = f"https://image.pollinations.ai/prompt/{prompt_url}?width=1024&height=768&nologo=true&seed=42"
    
    try:
        # Aumentiamo il timeout
        response = requests.get(api_url, timeout=60) 
        if response.status_code == 200:
            return response.content
    except:
        return None
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

# E nella UI, modifica come la visualizzi:
if 'immagine' in st.session_state:
    if st.session_state.immagine:
        # Streamlit caricherà l'immagine dal link da solo, molto più velocemente!
        st.image(st.session_state.immagine, use_container_width=True) 

# 2. Struttura del PDF sicura (Da inserire DOVE avevi il blocco PDF)
if 'analisi' in st.session_state and 'immagine' in st.session_state:
    if st.session_state.immagine:
        st.divider()
        if st.button("Genera il Dossier PDF"):
            try:
                pdf = FPDF(unit='mm', format=(400, 280))
                pdf.add_page()
                pdf.set_font("Arial", size=14)
                
                # Testo
                testo = st.session_state.analisi.encode('latin-1', 'replace').decode('latin-1')
                pdf.multi_cell(0, 10, txt=testo)
                
                # Immagine direttamente da memoria
                pdf.add_page()
                img_stream = io.BytesIO(st.session_state.immagine)
                pdf.image(img_stream, x=20, y=20, w=360)
                
                st.download_button("💾 Scarica Dossier PDF", 
                                   data=pdf.output(dest='S').encode('latin-1'), 
                                   file_name="opera.pdf")
            except Exception as e:
                st.error(f"Errore PDF: {e}")
