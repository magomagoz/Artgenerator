import streamlit as st
import urllib.parse
import requests
import random
from fpdf import FPDF
import os
import time

# --- Configurazione PDF ---
class PDF(FPDF):
    def header(self):
        if self.page_no() == 1:
            self.set_font('Arial', 'B', 22)
            self.cell(0, 20, 'IL PENNELLO DEL TEMPO', 0, 1, 'C')
            self.ln(5)
    
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Pagina {self.page_no()}', 0, 0, 'C')

def genera_analisi_ia(pittore, soggetto):
    """Interroga l'IA testuale gratuita di Pollinations per una recensione artistica."""
    prompt_testo = f"Agisci come un critico d'arte colto. Scrivi una breve recensione (massimo 80 parole) in italiano su un'opera che raffigura '{soggetto}' dipinta nello stile esatto di '{pittore}'. Evidenzia le tecniche peculiari di questo artista."
    url_testo = f"https://text.pollinations.ai/{urllib.parse.quote(prompt_testo)}"
    
    try:
        # Chiamata API testuale
        res = requests.get(url_testo, timeout=15)
        if res.status_code == 200:
            return res.text
    except Exception:
        pass
    
    # Testo di riserva in caso di timeout
    return f"L'opera cattura l'essenza di {soggetto} attraverso i rigorosi canoni estetici di {pittore}, in una composizione che riflette l'anima e la tecnica inconfondibile dell'artista."

def crea_pdf_completo(pittore, soggetto, immagine_bytes):
    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # --- PAGINA 1: ANALISI ---
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, f"Dossier: {soggetto.capitalize()}", 0, 1, 'L')
    pdf.set_font("Arial", 'I', 14)
    pdf.cell(0, 10, f"Stile e Tecnica: {pittore}", 0, 1, 'L')
    pdf.ln(10)
    
    # Recupero analisi dall'IA testuale
    with st.spinner("Il critico d'arte sta scrivendo la recensione..."):
        testo_analisi = genera_analisi_ia(pittore, soggetto)
    
    pdf.set_font("Arial", size=11)
    # Pulizia caratteri per evitare errori FPDF con gli accenti
    testo_pulito = testo_analisi.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 8, txt=testo_pulito)

    # --- PAGINA 2: IMMAGINE ---
    if immagine_bytes:
        pdf.add_page(orientation='L') 
        temp_img = f"temp_{random.randint(1,999)}.jpg"
        with open(temp_img, "wb") as f:
            f.write(immagine_bytes)
        
        pdf.image(temp_img, x=25, y=20, w=245) 
        os.remove(temp_img)
    
    return pdf.output(dest='S').encode('latin-1')

# --- INTERFACCIA STREAMLIT ---
st.set_page_config(page_title="Il Pennello del Tempo", page_icon="🎨")

if 'immagine_fatta' not in st.session_state:
    st.session_state.immagine_fatta = None

st.title("🎨 Il Pennello del Tempo")

col1, col2 = st.columns(2)
pittore_input = col1.text_input("Artista (Nome e Cognome)")
soggetto_input = col2.text_input("Soggetto")

if st.button("🎨 Crea Opera"):
    if pittore_input and soggetto_input:
        with st.spinner("L'IA sta dipingendo e studiando la tecnica..."):
            
            # --- PROMPT VISIVO UNIVERSALE CORRETTO ---
            # Abbiamo rimosso "oil on canvas". Diciamo all'IA di imitare la *vera* texture del pittore.
            prompt_visivo = (
                f"A perfect masterpiece of {soggetto_input} by {pittore_input}. "
                f"Strictly use the exact medium, surface texture, and visual language of {pittore_input}. "
                f"If the artist uses flat colors, make it flat. If they use thick impasto, use impasto. "
                f"Do not use generic oil brushstrokes unless it is the artist's historical style. "
                f"Highly detailed, masterpiece, 8k resolution."
            )
            
            url_immagine = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt_visivo)}?width=1024&height=768&nologo=true&seed={random.randint(1,999999)}"
            
            try:
                res_img = requests.get(url_immagine, timeout=45)
                if res_img.status_code == 200:
                    st.session_state.immagine_fatta = res_img.content
                    st.session_state.pittore_salvato = pittore_input
                    st.session_state.soggetto_salvato = soggetto_input
                    
                    avviso = st.empty()
                    for i in range(5, 0, -1):
                        avviso.info(f"⏳ Opera completata. Raffreddamento sistema: {i}s")
                        time.sleep(1)
                    avviso.empty()
                    st.rerun()
            except:
                st.error("Errore di connessione durante la generazione dell'immagine.")

if st.session_state.immagine_fatta:
    st.image(st.session_state.immagine_fatta, use_container_width=True)
    
    c1, c2 = st.columns(2)
    with c1:
        st.download_button("🖼️ Scarica Immagine", st.session_state.immagine_fatta, "opera.jpg", "image/jpeg")
    with c2:
        dati_pdf = crea_pdf_completo(st.session_state.pittore_salvato, st.session_state.soggetto_salvato, st.session_state.immagine_fatta)
        st.download_button("📄 Scarica Dossier Critico", dati_pdf, f"Dossier_{st.session_state.pittore_salvato}.pdf", "application/pdf")
