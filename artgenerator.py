Import streamlit as st
import urllib.parse
import requests
import random
from fpdf import FPDF  # CORRETTO: Sintassi di importazione esatta
import os
import time # Aggiungi questo import in alto
from duckduckgo_search import DDGS

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
    """Interroga l'IA di DuckDuckGo per una recensione artistica gratuita."""
    prompt = f"Agisci come un critico d'arte esperto di {pittore}. Scrivi una recensione (max 1000 parole) su questa interpretazione di '{soggetto}' fatto nello stile caratteristico di '{pittore}'. Sii poetico, colto e originale."
    try:
        with DDGS() as ddgs:
            # Usiamo il modello Llama 3 (gratuito e senza chiavi API)
            results = ddgs.chat(prompt, model="llama-3-70b")
            return results
    except Exception:
        return f"L'opera cattura l'essenza di {soggetto} attraverso i canoni estetici di {pittore}, in una fusione cromatica di raro vigore."

def crea_pdf_completo(pittore, soggetto, immagine_bytes):
    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # --- PAGINA 1: ANALISI ---
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, f"Dossier: {soggetto.capitalize()}", 0, 1, 'L')
    pdf.set_font("Arial", 'I', 14)
    pdf.cell(0, 10, f"Stile: {pittore}", 0, 1, 'L')
    pdf.ln(10)
    
    # Recupero analisi dall'IA
    with st.spinner("Il critico d'arte sta scrivendo..."):
        testo_analisi = genera_analisi_ia(pittore, soggetto)
    
    pdf.set_font("Arial", size=11)
    # Pulizia caratteri per evitare errori FPDF
    testo_pulito = testo_analisi.encode('latin-1', 'replace').decode('latin-1')
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
            # ... (logica di generazione prompt e richiesta URL)
                               
            prompt_artistico = (
                f"A definitive masterpiece that reimagines '{soggetto}' entirely through the unique visionary lens, "
                f"core compositional principles, and most famous recurring motifs of {pittore}. "
                f"The absolute primary focus is on how {pittore} would structure reality, color, and form. "
                f"This artwork must strictly integrate {pittore}'s signature aesthetic philosophy—whether it be heavy kinetic impasto, "
                f"delicate luminous glazes, abstract geometric fragmentation, or flat patterned linework—"
                f"applying it directly to '{soggetto}'. It must feel like an authentic discovery from {pittore}'s main body of work. "
                f"Highest quality detailed textures, 8k resolution."
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
            file_name=f"{st.session_state.soggetto_fatto}_{st.session_state.pittore_fatto}.jpg",
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
            file_name=f"Dossier_{st.session_state.pittore_fatto}.pdf",
            mime="application/pdf"
        )
