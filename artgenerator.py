import streamlit as st
import google.generativeai as genai
from fpdf import FPDF
from PIL import Image
import io

# Configurazione (Assicurati di impostare la tua API Key)
genai.configure(api_key="TUA_API_KEY")

def crea_pdf(testo):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, txt=testo.encode('latin-1', 'replace').decode('latin-1'))
    return pdf.output(dest='S').encode('latin-1')

st.title("🎨 Laboratorio di Stile Multimodale")

# 1. Input Multimodale
pittore = st.text_input("Pittore di riferimento:")
file_caricato = st.file_uploader("Carica un'immagine del soggetto da reinterpretare", type=['jpg', 'png'])

if st.button("Genera Analisi"):
    if pittore and file_caricato:
        img = Image.open(file_caricato)
        model = genai.GenerativeModel('gemini-1.5-flash') # Versione multimodale
        
        prompt = f"Sei un critico d'arte. Analizza questa immagine nello stile tecnico e compositivo di {pittore}."
        
        with st.spinner('Analisi artistica in corso...'):
            response = model.generate_content([prompt, img])
            st.markdown(response.text)
            
            # 2. Tasto Salvataggio PDF
            pdf_data = crea_pdf(response.text)
            st.download_button("💾 Salva Analisi in PDF", data=pdf_data, file_name="analisi_arte.pdf", mime="application/pdf")
    else:
        st.error("Inserisci il nome del pittore e carica un'immagine!")
