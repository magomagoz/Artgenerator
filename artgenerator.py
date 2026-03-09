import streamlit as st
from fpdf import FPDF
import io 
import os
import requests

# --- Configurazione API ---
HF_API_KEY = st.secrets["HF_API_KEY"]

def chiama_huggingface_testo(pittore, soggetto):
    """Genera l'analisi testuale con un prompt strutturato per Mistral."""
    api_url = "https://router.huggingface.co/hf-inference/models/mistralai/Mistral-7B-Instruct-v0.3"
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    
    # Prompt migliorato: diamo un ruolo preciso e istruzioni chiare
    prompt_formattato = f"<s>[INST] Sei un critico d'arte esperto. Scrivi un'analisi di 150 parole in italiano su come l'artista {pittore} dipingerebbe il soggetto '{soggetto}'. Descrivi tecnica, colori e atmosfera. [/INST]"
    
    payload = {
        "inputs": prompt_formattato,
        "parameters": {"max_new_tokens": 500, "temperature": 0.7, "return_full_text": False}
    }
    
    try:
        response = requests.post(api_url, headers=headers, json=payload)
        if response.status_code == 200:
            risultato = response.json()
            return risultato[0]['generated_text'].strip()
        else:
            return f"Nota: Il critico è momentaneamente assente (Errore {response.status_code})."
    except:
        return "Connessione al critico d'arte fallita."

def genera_immagine_huggingface(prompt):
    """Genera l'immagine usando Stable Diffusion XL."""
    api_url = "https://router.huggingface.co/hf-inference/models/stabilityai/stable-diffusion-xl-base-1.0"
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    payload = {"inputs": prompt}
    response = requests.post(api_url, headers=headers, json=payload)
    if response.status_code == 200:
        return response.content
    else:
        raise Exception(f"Errore Generazione Immagine.")

# --- Classe PDF ---
class PDF(FPDF):
    def header(self):
        if self.page_no() == 1:
            self.set_font('Arial', 'B', 24)
            self.cell(0, 20, 'IL PENNELLO DEL TEMPO', 0, 1, 'C')
            self.ln(10)

def crea_pdf_completo(pittore, soggetto, testo_analisi, immagine_bytes):
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, f"Soggetto: {soggetto} nello stile di {pittore}", 0, 1, 'L')
    pdf.ln(5)
    pdf.set_font("Arial", size=12)
    testo_pulito = testo_analisi.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 10, txt=testo_pulito)

    if immagine_bytes:
        pdf.add_page(orientation='L')
        with open("temp_image.jpg", "wb") as f:
            f.write(immagine_bytes)
        pdf.image("temp_image.jpg", x=10, y=10, w=277) 
        os.remove("temp_image.jpg")
    
    return pdf.output(dest='S').encode('latin-1')

# --- UI Streamlit ---
st.set_page_config(page_title="Il Pennello del Tempo", page_icon="🎨", layout="wide")

if os.path.exists("banner.png"):
    st.image("banner.png")

st.title("🎨 Il Pennello del Tempo: Analisi & Creazione")

# Session State
if 'analisi' not in st.session_state: st.session_state.analisi = None
if 'immagine' not in st.session_state: st.session_state.immagine = None
if 'pittore' not in st.session_state: st.session_state.pittore = ""
if 'soggetto' not in st.session_state: st.session_state.soggetto = ""

# Input
col1, col2 = st.columns(2)
p_in = col1.text_input("Scegli un Pittore")
s_in = col2.text_input("Soggetto da interpretare")

if st.button("Genera Opera"):
    if p_in and s_in:
        with st.spinner('Analizzando e Dipingendo...'):
            # 1. Testo
            st.session_state.analisi = chiama_huggingface_testo(p_in, s_in)
            # 2. Immagine
            try:
                prompt_img = f"A professional oil painting of {s_in} in the unique artistic style of {p_in}, masterpiece, highly detailed, vivid colors."
                st.session_state.immagine = genera_immagine_huggingface(prompt_img)
                st.session_state.pittore = p_in
                st.session_state.soggetto = s_in
            except Exception as e:
                st.error(str(e))
    else:
        st.warning("Inserisci entrambi i dati.")

# --- Layout di Visualizzazione ---
if st.session_state.analisi:
    st.divider()
    
    # 1. Analisi Sopra (A tutta larghezza)
    st.subheader("🖋️ Analisi del Critico")
    st.info(st.session_state.analisi)
    
    st.divider()
    
    # 2. Immagine Sotto (Grande)
    if st.session_state.immagine:
        st.subheader("🖼️ L'Opera d'Arte")
        st.image(st.session_state.immagine, use_container_width=True)
        
        # Bottone Download
        pdf_file = crea_pdf_completo(st.session_state.pittore, st.session_state.soggetto, st.session_state.analisi, st.session_state.immagine)
        st.download_button("💾 Scarica il PDF (Analisi + Immagine Landscape)", data=pdf_file, file_name=f"{st.session_state.pittore}.pdf", mime="application/pdf")
