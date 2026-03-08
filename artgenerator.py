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
    """Chiama l'API di Stability AI per generare un'immagine."""
    url = "https://api.stability.ai/v2beta/stable-image/generate/core"
    headers = {
        "authorization": f"Bearer {STABILITY_API_KEY}",
        "accept": "image/*"
    }
    files = {"none": ""}
    data = {
        "prompt": prompt,
        "output_format": "png"
    }
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
        # --- Generazione Testuale ---
        st.subheader("🖋️ Analisi Testuale")
        text_model = genai.GenerativeModel('gemini-2.5-flash')

        text_prompt = f"""
        Sei un critico d'arte ed esperto di tecniche pittoriche storiche. 
        Analizza il soggetto '{soggetto}' come se fosse stato dipinto da {pittore}.
        
        Struttura la risposta in tre punti:
        1. **Analisi Tecnica**: Descrivi la pennellata, l'uso del colore e la luce tipica dell'autore.
        2. **Composizione**: Spiega come verrebbe impostata la scena.
        3. **Interpretazione concettuale**: Spiega perché questa scelta stilistica valorizza il soggetto.
        
        Mantieni un tono accademico ma ispirato.
        """
        
        with st.spinner('Analizzando lo stile del maestro...'):
            try:
                text_response = text_model.generate_content(text_prompt)
                analisi_testuale = text_response.text
                st.markdown(analisi_testuale)
            except Exception as e:
                st.error(f"Errore durante la generazione dell'analisi testuale: {e}")
                analisi_testuale = "Errore durante la generazione dell'analisi."

        st.divider()
        
        # --- Generazione Immagine ---
        st.subheader("🖼️ Opera Generata")
        image_prompt_generator_model = genai.GenerativeModel('gemini-2.5-flash')
        
        image_description_prompt = f"""
        Basandoti sullo stile di {pittore} e sul soggetto '{soggetto}', 
        crea una descrizione dettagliata per un generatore di immagini AI. 
        La descrizione deve includere dettagli su:
        - tipo di immagine (dipinto ad olio, acquerello, scultura, ecc.)
        - colori dominanti e tavolozza
        - composizione e inquadratura
        - illuminazione e atmosfera
        - elementi specifici del pittore (es. pennellate, figure distorte, chiaroscuro)
        - dettagli sul soggetto '{soggetto}' nel contesto di quello stile.
        La descrizione deve essere in inglese e avere una lunghezza massima di 150 parole.
        """
        
        with st.spinner('Il maestro sta dipingendo...'):
            try:
                # Generazione prompt per Stability
                image_description_response = image_prompt_generator_model.generate_content(image_description_prompt)
                final_image_prompt = image_description_response.text
                
                # Chiamata a Stability AI
                immagine_bytes = genera_immagine_stability(final_image_prompt)
                
                # Visualizzazione
                st.image(immagine_bytes, caption=f"Reinterpretazione di {pittore}")
                
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
                
            except Exception as e:
                st.error(f"Errore durante la generazione dell'immagine: {e}")
    else:
        st.warning("Per favore, compila entrambi i campi.")
