import streamlit as st
import urllib.parse
import requests
import random
from fpdf import FPDF
import os
import time

# --- Funzione PDF Avanzata ---
class PDF(FPDF):
    def header(self):
        if self.page_no() == 1:
            self.set_font('Arial', 'B', 24)
            self.cell(0, 20, 'IL PENNELLO DEL TEMPO', 0, 1, 'C')
            self.ln(10)
    
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Pagina {self.page_no()}', 0, 0, 'C')

def genera_analisi_ia(pittore, soggetto):
    """Interroga l'IA testuale gratuita di Pollinations per una recensione specifica."""
    # Chiediamo all'IA di generare una vera critica d'arte
    prompt_testo = f"Agisci come un critico d'arte esperto di {pittore}. Scrivi una recensione elegante e tecnica di massimo 150 parole in italiano su un'opera che raffigura '{soggetto}' realizzata seguendo fedelmente lo stile, la filosofia e i motivi iconici di {pittore}."
    url_testo = f"https://text.pollinations.ai/{urllib.parse.quote(prompt_testo)}"
    
    try:
        res = requests.get(url_testo, timeout=15)
        if res.status_code == 200:
            return res.text
    except:
        pass
    return f"L'opera analizzata traspone il soggetto '{soggetto}' nel linguaggio visivo tipico di {pittore}, fondendo forma e concetto in un'armonia cromatica coerente con la storia del maestro."

def crea_pdf_completo(pittore, soggetto, immagine_bytes):
    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # --- PAGINA 1: ANALISI CRITICA ---
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, f"Dossier Critico: {soggetto.capitalize()}", 0, 1, 'L')
    pdf.set_font("Arial", 'I', 14)
    pdf.cell(0, 10, f"Stile: {pittore}", 0, 1, 'L')
    pdf.ln(10)
    
    with st.spinner("Il critico sta redigendo l'analisi..."):
        testo_analisi = genera_analisi_ia(pittore, soggetto)
    
    pdf.set_font("Arial", size=11)
    # Pulizia caratteri per FPDF (latin-1)
    testo_pulito = testo_analisi.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 8, txt=testo_pulito)

    # --- PAGINA 2: L'OPERA (Formato pieno, no ritaglio) ---
    if immagine_bytes:
        pdf.add_page(orientation='L') 
        temp_img = f"temp_{random.randint(1,999)}.jpg"
        with open(temp_img, "wb") as f:
            f.write(immagine_bytes)
        
        # Centratura ottimale per 1024x768 su A4 Landscape
        pdf.image(temp_img, x=25, y=20, w=245) 
        os.remove(temp_img)
    
    return pdf.output(dest='S').encode('latin-1')

# --- UI Streamlit ---
st.set_page_config(page_title="Il Pennello del Tempo", page_icon="🎨", layout="wide")

if 'immagine_fatta' not in st.session_state:
    st.session_state.immagine_fatta = None

st.title("🎨 Il Pennello del Tempo")

col1, col2 = st.columns(2)
pittore_input = col1.text_input("🎨 Nome completo del Pittore")
soggetto_input = col2.text_input("Soggetto da dipingere")

if st.button("Genera Visione Artistica"):
    if pittore_input and soggetto_input:
        st.session_state.immagine_fatta = None 
        with st.spinner(f"Il maestro {pittore_input} sta dipingendo..."):
            
            # PROMPT CORRETTO: Rimosso "oil on canvas" generico. 
            # Ora istruiamo l'IA a usare il medium specifico dell'artista scelto.
            prompt_artistico = (
                f"A professional masterpiece of '{soggetto_input}' by {pittore_input}. "
                f"Strictly adhere to the exact historical visual language, surface texture, and medium of {pittore_input}. "
                f"Incorporate the most famous recurring motifs and conceptual symbols of the artist. "
                f"High resolution, authentic artistic style, museum quality, highly detailed."
            )
            
            prompt_encoded = urllib.parse.quote(prompt_artistico)
            image_url = f"https://image.pollinations.ai/prompt/{prompt_encoded}?width=1024&height=768&nologo=true&seed={random.randint(1, 999999)}"
            
            try:
                response = requests.get(image_url, timeout=45) 
                if response.status_code == 200:
                    st.session_state.immagine_fatta = response.content
                    st.session_state.pittore_fatto = pittore_input
                    st.session_state.soggetto_fatto = soggetto_input
                    
                    placeholder = st.empty()
                    for seconds in range(5, 0, -1):
                        placeholder.warning(f"⏳ Raffreddamento sistema: {seconds}s")
                        time.sleep(1)
                    placeholder.empty()
                    st.rerun() 
            except:
                st.error("Errore di connessione.")

if st.session_state.immagine_fatta:
    st.image(st.session_state.immagine_fatta, use_container_width=True)
    
    c_dl1, c_dl2 = st.columns(2)
    with c_dl1:
        st.download_button("🖼️ Scarica JPG", st.session_state.immagine_fatta, "opera.jpg", "image/jpeg")
    with c_dl2:
        pdf_data = crea_pdf_completo(st.session_state.pittore_fatto, st.session_state.soggetto_fatto, st.session_state.immagine_fatta)
        st.download_button("📄 Scarica Dossier PDF", pdf_data, f"Dossier_{st.session_state.pittore_fatto}.pdf", "application/pdf")
