import streamlit as st
import google.generativeai as genai
from fpdf import FPDF
import io 
import os
import requests

# --- Configurazione API ---
genai.configure(api_key=st.secrets["API_KEY"])
#STABILITY_API_KEY = st.secrets["STABILITY_API_KEY"]
HF_API_KEY = st.secrets["HF_API_KEY"]

#def genera_immagine_stability(prompt):
    #"""Chiama l'API di Stability AI per generare un'immagine."""
    #url = "https://api.stability.ai/v2beta/stable-image/generate/core"
    #headers = {
        #"authorization": f"Bearer {STABILITY_API_KEY}",
        #"accept": "image/*"
    #}
    #files = {"none": ""}
    #data = {
        #"prompt": prompt,
        #"output_format": "png"
    #}
    #response = requests.post(url, headers=headers, files=files, data=data)
    #if response.status_code == 200:
        #return response.content
    #else:
        #raise Exception(f"Errore Stability AI: {response.text}")

def genera_immagine_huggingface(prompt):
    # Nuovo URL aggiornato secondo le nuove direttive di Hugging Face
    api_url = "https://router.huggingface.co/hf-inference/models/stabilityai/stable-diffusion-xl-base-1.0"
    headers = {"Authorization": f"Bearer {st.secrets['HF_API_KEY']}"}
    
    payload = {"inputs": prompt}
    response = requests.post(api_url, headers=headers, json=payload)
    
    if response.status_code == 200:
        return response.content
    else:
        raise Exception(f"Errore Hugging Face: {response.text}")



# --- Funzione PDF Avanzata ---
class PDF(FPDF):
    def header(self):
        # Titolo grande nella prima pagina
        if self.page_no() == 1:
            self.set_font('Arial', 'B', 24)
            self.cell(0, 20, 'IL PENNELLO DEL TEMPO', 0, 1, 'C')
            self.ln(10)
    
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Pagina {self.page_no()}', 0, 0, 'C')

def crea_pdf_completo(pittore, soggetto, testo_analisi, immagine_bytes):
    pdf = PDF()
    
    # --- PAGINA 1: ANALISI ---
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, f"Soggetto: {soggetto} nello stile di {pittore}", 0, 1, 'L')
    pdf.ln(5)
    
    pdf.set_font("Arial", size=12)
    # Pulizia testo per PDF (evita errori caratteri speciali)
    testo_pulito = testo_analisi.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 10, txt=testo_pulito)

    # --- PAGINA 2: IMMAGINE LANDSCAPE ---
    if immagine_bytes:
        # Aggiungiamo una pagina in orientamento Landscape ('L')
        pdf.add_page(orientation='L')
        
        # ---> CORREZIONE: usiamo .jpg invece di .png <---
        with open("temp_image.jpg", "wb") as f:
            f.write(immagine_bytes)
        
        # Inseriamo l'immagine a tutta pagina
        pdf.image("temp_image.jpg", x=10, y=10, w=277) 
        os.remove("temp_image.jpg")
    
    return pdf.output(dest='S').encode('latin-1')


# --- Configurazione Pagina Streamlit ---
st.set_page_config(page_title="Il Pennello del Tempo", page_icon="🎨", layout="wide")
st.image("banner.png")

st.divider()
st.title("🎨 Il Pennello del Tempo: Analisi & Creazione")

# --- Inizializzazione Session State ---
if 'analisi_generata' not in st.session_state:
    st.session_state.analisi_generata = None
if 'immagine_generata' not in st.session_state:
    st.session_state.immagine_generata = None
if 'pittore_corrente' not in st.session_state:
    st.session_state.pittore_corrente = ""
if 'soggetto_corrente' not in st.session_state:
    st.session_state.soggetto_corrente = ""

# --- Controlli Input ---
col1, col2 = st.columns(2)
pittore = col1.text_input("Scegli un Pittore")
soggetto = col2.text_input("Soggetto da interpretare")

# --- Bottone Genera ---
if st.button("Genera Interpretazione Artistica"):
    if pittore and soggetto:
        # Inizializziamo analisi_testuale come stringa vuota o messaggio di cortesia
        analisi_testuale = "Analisi non disponibile (limite di quota raggiunto), ma ecco la tua opera!"
        
        # 1. TENTATIVO GENERAZIONE TESTUALE (Gemini)
        with st.spinner('Interpellando il critico d\'arte...'):
            try:
                # Se 2.5 funziona per te, manteniamo quello
                text_model = genai.GenerativeModel('gemini-2.5-flash')
                text_prompt = f"Analizza brevemente '{soggetto}' nello stile di {pittore}."
                text_response = text_model.generate_content(text_prompt)
                analisi_testuale = text_response.text
                
                # Salviamo nello stato solo se ha successo
                st.session_state.analisi_generata = analisi_testuale
                st.subheader("🖋️ Analisi Testuale")
                st.markdown(analisi_testuale)
            except Exception as e:
                # Se Gemini va in errore 429, mostriamo un avviso ma NON fermiamo lo script
                st.warning("Il critico d'arte è occupato (quota piena), procedo direttamente con il dipinto!")
                st.session_state.analisi_generata = analisi_testuale # Messaggio di fallback

        st.divider()
        
        # 2. GENERAZIONE IMMAGINE (Sempre eseguita)
        st.subheader("🖼️ Opera Generata")
        # Prompt costruito direttamente per non usare Gemini (Zero Quota)
        final_prompt = f"A professional oil painting of {soggetto} in the style of {pittore}, masterpiece, high resolution."
        
        with st.spinner('Il maestro sta dipingendo...'):
            try:
                # Usiamo Hugging Face che è più generoso
                immagine_bytes = genera_immagine_huggingface(final_prompt)
                st.session_state.immagine_generata = immagine_bytes
                st.image(immagine_bytes, caption=f"Interpretazione di {pittore}")
                
                # Salviamo i nomi correnti per il PDF
                st.session_state.pittore_corrente = pittore
                st.session_state.soggetto_corrente = soggetto
                
                # Generazione PDF (usando le variabili dello stato o locali)
                pdf_data = crea_pdf_completo(pittore, soggetto, st.session_state.analisi_generata, immagine_bytes)
                st.download_button("💾 Scarica PDF Artistico", data=pdf_data, 
                                   file_name=f"{pittore}_{soggetto}.pdf", mime="application/pdf")
            except Exception as e:
                st.error(f"Errore Immagine: {e}")
    else:
        st.warning("Per favore, compila entrambi i campi.")
