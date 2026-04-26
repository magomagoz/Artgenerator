import streamlit as st
import google.generativeai as genai
from fpdf import FPDF
import io 
import os
import requests

# --- Configurazione API ---
genai.configure(api_key=st.secrets["API_KEY"])
STABILITY_API_KEY = st.secrets["STABILITY_API_KEY"]

def genera_immagine_stability(prompt):
    url = "https://api.stability.ai/v2beta/stable-image/generate/core"
    headers = {
        "authorization": f"Bearer {STABILITY_API_KEY}",
        "accept": "image/*"
    }
    files = {"none": ""}
    data = {"prompt": prompt, "output_format": "png"}
    response = requests.post(url, headers=headers, files=files, data=data)
    if response.status_code == 200:
        return response.content
    else:
        raise Exception(f"Errore Stability AI: {response.text}")

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
        with open("temp_image.png", "wb") as f:
            f.write(immagine_bytes)
        
        # Inseriamo l'immagine a tutta pagina (Landscape A4 è ~297mm x 210mm)
        # Lasciamo un piccolo margine di 10mm
        pdf.image("temp_image.png", x=10, y=10, w=277) 
        os.remove("temp_image.png")
    
    return pdf.output(dest='S').encode('latin-1')

# --- Configurazione Streamlit ---
st.set_page_config(page_title="Il Pennello del Tempo", page_icon="🎨", layout="wide")

if os.path.exists("banner.png"):
    st.image("banner.png")
else:
    st.title("🎨 Il Pennello del Tempo")

# --- Inizializzazione Session State ---
if 'analisi_generata' not in st.session_state:
    st.session_state.analisi_generata = None
if 'immagine_generata' not in st.session_state:
    st.session_state.immagine_generata = None
if 'pittore_corrente' not in st.session_state:
    st.session_state.pittore_corrente = ""
if 'soggetto_corrente' not in st.session_state:
    st.session_state.soggetto_corrente = ""

# --- Input ---
col1, col2 = st.columns(2)
pittore_input = col1.text_input("Pittore (es. Vincent van Gogh)")
soggetto_input = col2.text_input("Soggetto (es. un telefono cellulare)")

# --- Logica Generazione ---
if st.button("Genera Interpretazione Artistica e Immagine"):
    if pittore_input and soggetto_input:
        with st.spinner('Analizzando e dipingendo...'):
            try:
                # 1. Testo
                text_model = genai.GenerativeModel('gemini-2.5-flash')
                text_prompt = f"Critico d'arte: analizza '{soggetto_input}' nello stile di {pittore_input}. 3 punti: Tecnica, Composizione, Concetto."
                text_response = text_model.generate_content(text_prompt)
                
                # 2. Immagine
                image_model = genai.GenerativeModel('gemini-2.5-flash')
                img_desc_prompt = f"Create a detailed English prompt for an AI image generator: '{soggetto_input}' painted by {pittore_input}. focus on brushwork and lighting."
                img_desc_res = image_model.generate_content(img_desc_prompt)
                
                img_bytes = genera_immagine_stability(img_desc_res.text)

                # Salvataggio in Session State
                st.session_state.analisi_generata = text_response.text
                st.session_state.immagine_generata = img_bytes
                st.session_state.pittore_corrente = pittore_input
                st.session_state.soggetto_corrente = soggetto_input
                
            except Exception as e:
                st.error(f"Errore: {e}")
    else:
        st.warning("Inserisci entrambi i dati.")

# --- Visualizzazione Persistente ---
if st.session_state.analisi_generata:
    st.divider()
    col_out1, col_out2 = st.columns([1, 1])
    
    with col_out1:
        st.subheader("🖋️ Analisi Testuale")
        st.markdown(st.session_state.analisi_generata)
    
    with col_out2:
        st.subheader("🖼️ Opera Generata")
        st.image(st.session_state.immagine_generata)
        
        # Generazione PDF
        pdf_data = crea_pdf_completo(
            st.session_state.pittore_corrente,
            st.session_state.soggetto_corrente,
            st.session_state.analisi_generata,
            st.session_state.immagine_generata
        )
        
        st.download_button(
            label="💾 Scarica PDF Artistico",
            data=pdf_data,
            file_name=f"{st.session_state.pittore_corrente}_{st.session_state.soggetto_corrente}.pdf",
            mime="application/pdf"
        )


