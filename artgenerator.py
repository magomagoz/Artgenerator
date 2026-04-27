import streamlit as st
import urllib.parse
import requests
import random
from fpdf import FPDF  # CORRETTO: Sintassi di importazione esatta
import os
import time # Aggiungi questo import in alto
#from duckduckgo_search import DDGS

# --- Funzione PDF Avanzata (Adattata per sola Immagine/Titolo) ---
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
    """Interroga l'IA testuale di Pollinations con parametri di pulizia testo."""
    # Usiamo il parametro cache=True e model='openai' (o lasciamo default) per stabilità
    prompt_testo = (f"Agisci come un critico d'arte esperto di {pittore}. "
                    f"Scrivi una recensione approfondita, colta e originale in italiano (circa 500 parole) "
                    f"sull'opera '{soggetto}' realizzata nello stile esatto di {pittore}. "
                    f"Analizza tecnica, uso del colore e filosofia.")
    
    # Aggiungiamo ?model=openai per usare un modello più capace di generare testi lunghi
    url_testo = f"https://text.pollinations.ai/{urllib.parse.quote(prompt_testo)}?model=openai"
    
    try:
        res = requests.get(url_testo, timeout=30) # Aumentato timeout per testi lunghi
        if res.status_code == 200:
            testo = res.text
            if testo and len(testo) > 50: # Verifichiamo che non sia vuoto
                return testo
    except Exception as e:
        st.error(f"Errore critico: {e}")
    
    return f"L'opera analizzata traspone il soggetto '{soggetto}' nel linguaggio visivo tipico di {pittore}..."

def crea_pdf_completo(pittore, soggetto, immagine_bytes):
    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # --- PAGINA 1: ANALISI ---
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, f"Dossier: {soggetto.capitalize()} del maestro {pittore}", 0, 1, 'L')
    pdf.set_font("Arial", 'I', 14)
    pdf.cell(0, 10, f"Stile: {pittore}", 0, 1, 'L')
    pdf.ln(10)
    
    # Recupero analisi dall'IA
    with st.spinner("Il critico d'arte sta scrivendo..."):
        testo_analisi = genera_analisi_ia(pittore, soggetto)
    
    pdf.set_font("Arial", size=11)
    testo_pulito = testo_analisi.replace('’', "'").replace('“', '"').replace('”', '"')
    testo_pulito = testo_pulito.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 8, txt=testo_pulito)

    # --- PAGINA 2: IMMAGINE (Centrata e non tagliata) ---
    if immagine_bytes:
        pdf.add_page(orientation='L') 
        temp_img = f"temp_{random.randint(1,999)}.jpg"
        with open(temp_img, "wb") as f:
            f.write(immagine_bytes)
        
        # Parametri ottimizzati: x=25, y=20, larghezza=245 (su 297mm totali)
        # Questo garantisce che non venga mai tagliata la parte inferiore
        pdf.image(temp_img, x=25, y=20, w=245) 
        os.remove(temp_img)
    
    return pdf.output(dest='S').encode('latin-1')

# --- Configurazione Base ---
st.set_page_config(page_title="Il Pennello del Tempo", page_icon="🎨", layout="wide")

# Assicurati di avere l'immagine "banner3.png" nella stessa cartella!
try:
    st.image("banner3.png")
except:
    st.warning("Banner non trovato. Assicurati che 'banner3.png' sia nella cartella del progetto.")

# --- Inizializzazione Unica dello Stato della Sessione ---
if 'immagine_fatta' not in st.session_state:
    st.session_state.immagine_fatta = None
if 'pittore_fatto' not in st.session_state:
    st.session_state.pittore_fatto = ""
if 'soggetto_fatto' not in st.session_state:
    st.session_state.soggetto_fatto = ""

# --- Input Utente ---
col1, col2 = st.columns(2)
pittore = col1.text_input("🎨 Nome completo del Pittore (movimento artistico e/o tecnica specifica)")
soggetto = col2.text_input("Soggetto da dipingere")

if st.button("Genera Visione Artistica"):
    if pittore and soggetto:
        st.session_state.immagine_fatta = None 

        with st.spinner(f"Il maestro {pittore} sta dipingendo..."):
            prompt_artistico = (
                f"A definitive professional masterpiece of '{soggetto}' by {pittore}. "
                f"Strictly adopt the authentic visual language, historical medium, and specific surface texture of {pittore}. "
                f"If the artist uses flat graphics, use flat graphics. If they use glazes, use glazes. "
                f"Incorporate iconic motifs and the philosophical essence of {pittore}'s work. "
                f"Museum quality, highly detailed, 8k resolution, authentic aesthetic."
            )
            
            prompt_encoded = urllib.parse.quote(prompt_artistico)
            seed = random.randint(1, 999999)
            
            image_url = f"https://image.pollinations.ai/prompt/{prompt_encoded}?width=1024&height=768&nologo=true&seed={seed}"
            
            try:
                response = requests.get(image_url, timeout=45) 
                
                if response.status_code == 200:
                    st.session_state.immagine_fatta = response.content
                    st.session_state.pittore_fatto = pittore
                    st.session_state.soggetto_fatto = soggetto
                    
                    # --- LOGICA DEL TIMER ---
                    placeholder = st.empty()
                    for seconds in range(10, 0, -1):
                        placeholder.warning(f"⏳ Pronto per una nuova opera tra {seconds} secondi.")
                        time.sleep(1)
                    placeholder.success("✅ Pronto per una nuova generazione!")
                    
                    st.rerun() 
            except Exception as e:
                st.error("Errore di connessione: L'API ci ha messo troppo tempo a rispondere.")
    else:
        st.warning("Inserisci entrambi i campi.")

# --- MOSTRA L'IMMAGINE E I PULSANTI DOWNLOAD ---
if st.session_state.immagine_fatta is not None:
    st.image(st.session_state.immagine_fatta, 
             caption=f"{st.session_state.soggetto_fatto} in stile {st.session_state.pittore_fatto}", 
             use_container_width=True)
    
    st.success("Opera completata!")
    
    # Creiamo due colonne per affiancare i bottoni di download
    col_dl1, col_dl2 = st.columns(2)
    
    with col_dl1:
        # Bottone Download Immagine JPEG
        st.download_button(
            label="🖼️ Scarica solo l'Immagine (JPG)",
            data=st.session_state.immagine_fatta,
            file_name=f"Soggetto:_{st.session_state.soggetto_fatto}_realizzato_dal_maestro_{st.session_state.pittore_fatto}.jpg",
            mime="image/jpeg"
        )
        
    with col_dl2:
        # Generazione e Bottone Download PDF
        pdf_data = crea_pdf_completo(
            st.session_state.pittore_fatto,
            st.session_state.soggetto_fatto,
            st.session_state.immagine_fatta
        )
        
        st.download_button(
            label="📄 Scarica Dossier PDF",
            data=pdf_data,
            file_name=f"Recensione_critica_di_{st.session_state.soggetto_fatto}_del_maestro_{st.session_state.pittore_fatto}.pdf",
            mime="application/pdf"
        )
