import streamlit as st
import urllib.parse
import requests
import random
from fpdf import FPDF 
import os
import time 
import re

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
    # Prompt anti-allucinazione per il testo
    prompt_testo = (
        f"Agisci come un critico d'arte esperto. Scrivi una recensione tecnica di 400 parole in italiano "
        f"sull'opera '{soggetto}' realizzata da {pittore}. "
        f"IMPORTANTE: L'opera rappresenta solo ed esclusivamente '{soggetto}'. "
        f"Non menzionare ballerine, fiori o altri soggetti tipici se non sono il soggetto richiesto. "
        f"Analizza pennellate, luce e filosofia di {pittore} applicate a questo specifico lavoro."
    )
    
    url_testo = f"https://text.pollinations.ai/{urllib.parse.quote(prompt_testo)}?model=openai"
    
    try:
        res = requests.get(url_testo, timeout=30)
        if res.status_code == 200:
            testo = res.text
            # Pulizia caratteri speciali per evitare crash FPDF
            testo = testo.replace('\xa0', ' ').replace('\u202f', ' ').replace('\u200b', '')
            testo = testo.replace('’', "'").replace('“', '"').replace('”', '"').replace('–', '-')
            return testo
    except Exception:
        pass
    return f"Analisi critica dell'opera '{soggetto}' nello stile inconfondibile di {pittore}."
    
def crea_pdf_completo(pittore, soggetto, immagine_bytes):
    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # --- PAGINA 1: TESTO ---
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, f"Dossier: {soggetto.capitalize()} del maestro {pittore}", 0, 1, 'L')
    pdf.set_font("Arial", 'I', 14)
    pdf.cell(0, 10, f"Stile: {pittore}", 0, 1, 'L')
    pdf.ln(10)

    with st.spinner("Il critico d'arte sta analizzando l'opera..."):
        testo_analisi = genera_analisi_ia(pittore, soggetto)
    
    # Pulizia definitiva per FPDF (rimozione tag e conversione codifica)
    testo_pulito = re.sub(r'<[^>]+>', '', testo_analisi) 
    testo_per_pdf = testo_pulito.encode('latin-1', 'replace').decode('latin-1').replace('?', '')
        
    pdf.set_font("Arial", size=11)
    pdf.multi_cell(0, 8, txt=testo_per_pdf)

    # --- PAGINA 2: IMMAGINE ---
    if immagine_bytes:
        pdf.add_page(orientation='L') 
        temp_img = f"temp_{random.randint(1,999)}.jpg"
        with open(temp_img, "wb") as f:
            f.write(immagine_bytes)
        
        # Posizionamento immagine centrata
        pdf.image(temp_img, x=25, y=20, w=245) 
        os.remove(temp_img)
    
    return pdf.output(dest='S').encode('latin-1')

# --- Interfaccia Streamlit ---
st.set_page_config(page_title="Il Pennello del Tempo", page_icon="🎨", layout="wide")

try:
    st.image("banner3.png")
except:
    st.title("🎨 Il Pennello del Tempo")

# Inizializzazione sessione
if 'immagine_fatta' not in st.session_state:
    st.session_state.immagine_fatta = None

col1, col2 = st.columns(2)
pittore = col1.text_input("🎨 Artista / Movimento (es. Magritte, Surrealismo)")
soggetto = col2.text_input("Soggetto da dipingere (es. Roma, Un computer)")

if st.button("Genera Visione Artistica"):
    if pittore and soggetto:
        with st.spinner(f"Il maestro {pittore} sta preparando la tela..."):
            # PROMPT RINFORZATO PER COERENZA VISIVA
            prompt_artistico = (
                f"A centered, symmetrical professional masterpiece depicting ONLY '{soggetto}' as the absolute main focus. "
                f"The subject '{soggetto}' is placed in the dead center of the frame. "
                f"Style: exact recreation of {pittore}'s unique visual language and historical medium. "
                f"Strictly avoid any typical subjects of {pittore} (like dancers or flowers) if they are not '{soggetto}'. "
                f"Museum quality, 8k resolution, authentic aesthetic."
            )
            
            prompt_encoded = urllib.parse.quote(prompt_artistico)
            seed = random.randint(1, 999999)
            image_url = f"https://image.pollinations.ai/prompt/{prompt_encoded}?width=1024&height=768&nologo=true&seed={seed}"
            
            try:
                response = requests.get(image_url, timeout=40)
                if response.status_code == 200:
                    st.session_state.immagine_fatta = response.content
                    st.session_state.pittore_fatto = pittore
                    st.session_state.soggetto_fatto = soggetto
                    st.rerun()
            except:
                st.error("Il server è occupato. Riprova tra 10 secondi.")
    else:
        st.warning("Inserisci sia l'artista che il soggetto.")

# Visualizzazione e Download
if st.session_state.immagine_fatta:
    st.image(st.session_state.immagine_fatta, use_container_width=True)
    st.success(f"Opera completata: {st.session_state.soggetto_fatto} in stile {st.session_state.pittore_fatto}")
    
    col_dl1, col_dl2 = st.columns(2)
    
    with col_dl1:
        st.download_button(
            label="🖼️ Scarica Immagine (JPG)",
            data=st.session_state.immagine_fatta,
            file_name=f"{st.session_state.pittore_fatto}_interpreta_{st.session_state.soggetto_fatto}.jpg",
            mime="image/jpeg"
        )
        
    with col_dl2:
        pdf_data = crea_pdf_completo(
            st.session_state.pittore_fatto,
            st.session_state.soggetto_fatto,
            st.session_state.immagine_fatta
        )
        st.download_button(
            label="📄 Scarica Dossier PDF",
            data=pdf_data,
            file_name=f"Dossier_{st.session_state.soggetto_fatto}.pdf",
            mime="application/pdf"
        )
