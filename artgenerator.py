import streamlit as st
import urllib.parse
import requests
import random
from fpdf import FPDF  # CORRETTO: Sintassi di importazione esatta
import os

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

def crea_pdf_completo(pittore, soggetto, immagine_bytes):
    pdf = PDF()
    
    # --- PAGINA 1: TITOLO ---
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, f"Soggetto: {soggetto}", 0, 1, 'L')
    pdf.set_font("Arial", 'I', 14)
    pdf.cell(0, 10, f"Interpretato nello stile di: {pittore}", 0, 1, 'L')
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, txt="Di seguito, l'interpretazione visiva originale generata dall'Intelligenza Artificiale, che unisce le tecniche storiche del maestro con il soggetto richiesto.")

    # --- PAGINA 2: IMMAGINE LANDSCAPE ---
    if immagine_bytes:
        pdf.add_page(orientation='L')
        # Usiamo un nome temporaneo sicuro
        temp_img_path = "temp_image.jpg"
        with open(temp_img_path, "wb") as f:
            f.write(immagine_bytes)
        
        # Inseriamo l'immagine a tutta pagina
        pdf.image(temp_img_path, x=10, y=10, w=277) 
        os.remove(temp_img_path) # Puliamo il file temporaneo
    
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
pittore = col1.text_input("🎨 Pittore (es. Van Gogh, Caravaggio)")
soggetto = col2.text_input("Soggetto (es. una città futuristica)")

if st.button("Genera Visione Artistica"):
    if pittore and soggetto:
        # Cancelliamo la vecchia immagine appena premiamo il tasto
        st.session_state.immagine_fatta = None 

        with st.spinner(f"Il maestro {pittore} sta dipingendo..."):
                    
            prompt_artistico = (
                f"I am the painter {pittore}, a master of my unique creative style and my historical era. "
                f"I will now employ all my signature techniques and artistic vision to create an unmistakable and authentic signature style of '{soggetto}', that is prominently displayed in the center of the frame. "
                f"featuring my specific brushwork, use of light, historical color palette, and emotional depth. "
                f"Oil on canvas, museum quality, 8k resolution, highly detailed textures."
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
                    st.rerun() 
                else:
                    st.error("Servizio momentaneamente occupato. Il server gratuito è sovraccarico, riprova tra poco.")
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
