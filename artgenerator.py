import streamlit as st
import urllib.parse
import requests
import random
#import FPDF as fpdf
import io 
import os
import requests




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





# Configurazione base
st.set_page_config(page_title="Il Pennello del Tempo", page_icon="🎨", layout="wide")
st.image("banner3.png")
#st.title("🎨 Il Pennello del Tempo")

# Inizializziamo lo stato della sessione se non esiste
if 'immagine_fatta' not in st.session_state:
    st.session_state.immagine_fatta = None
if 'pittore_fatto' not in st.session_state:
    st.session_state.pittore_fatto = ""
if 'soggetto_fatto' not in st.session_state:
    st.session_state.soggetto_fatto = ""



# --- Inizializzazione Session State ---
if 'analisi_generata' not in st.session_state:
    st.session_state.analisi_generata = None
if 'immagine_generata' not in st.session_state:
    st.session_state.immagine_generata = None
if 'pittore_corrente' not in st.session_state:
    st.session_state.pittore_corrente = ""
if 'soggetto_corrente' not in st.session_state:
    st.session_state.soggetto_corrente = ""




# Input utente
col1, col2 = st.columns(2)
pittore = col1.text_input("🎨 Pittore (es. Van Gogh, Caravaggio)")
soggetto = col2.text_input("Soggetto (es. una città futuristica)")

if st.button("Genera Visione Artistica"):
    if pittore and soggetto:
        
        # --- NOVITÀ: Cancelliamo la vecchia immagine appena premiamo il tasto ---
        st.session_state.immagine_fatta = None 
        # ------------------------------------------------------------------------

        with st.spinner(f"Il maestro {pittore} sta dipingendo..."):
            # 1. Creiamo il prompt
            
            prompt_artistico = (
                #f"A central, extreme close-up masterpiece painting exclusively focused on '{soggetto}' as the absolute main subject. "
                f"The '{soggetto}' is prominently displayed in the center of the frame. "
                f"I am the painter {pittore}, a master of my unique creative style and my historical era. "
                f"I will now employ all my signature techniques and artistic vision to create an unmistakable and authentic signature style of '{soggetto}', "
                f"featuring my specific brushwork, use of light, historical color palette, and emotional depth. "
                f"Oil on canvas, museum quality, 8k resolution, highly detailed textures."
            )
            
            prompt_encoded = urllib.parse.quote(prompt_artistico)
            seed = random.randint(1, 999999)
            
            # 2. URL del servizio
            image_url = f"https://image.pollinations.ai/prompt/{prompt_encoded}?width=1024&height=768&nologo=true&seed={seed}"
            
            try:
                # Ho alzato leggermente il timeout per evitare che Pollinations si arrenda troppo presto
                response = requests.get(image_url, timeout=45) 
                
                if response.status_code == 200:
                    # SALVIAMO NELLO STATO DELLA SESSIONE
                    st.session_state.immagine_fatta = response.content
                    st.session_state.pittore_fatto = pittore
                    st.session_state.soggetto_fatto = soggetto
                    
                    # Forziamo un ricaricamento della pagina per far apparire subito l'immagine pulita
                    st.rerun() 
                else:
                    st.error("Servizio momentaneamente occupato. Il server gratuito è sovraccarico, riprova tra poco.")
            except Exception as e:
                st.error(f"Errore di connessione: L'API ci ha messo troppo tempo a rispondere.")
    else:
        st.warning("Inserisci entrambi i campi.")

# MOSTRA L'IMMAGINE PERSISTENTE (se esiste nello stato della sessione)
if st.session_state.immagine_fatta is not None:
    st.image(st.session_state.immagine_fatta, 
             caption=f"{st.session_state.soggetto_fatto} in stile {st.session_state.pittore_fatto}", 
             use_container_width=True)
    
    st.success("Opera completata!")
    
        
    # Generazione PDF
    pdf_data = crea_pdf_completo(
        st.session_state.pittore_corrente,
        st.session_state.soggetto_corrente,
        st.session_state.analisi_generata,
        st.session_state.immagine_generata
    )
        
    # Il pulsante di download ora non farà sparire nulla
    st.download_button(
        label="💾 Scarica questa opera",
        data=st.session_state.immagine_fatta,
        file_name=f"{st.session_state.soggetto_fatto}_{st.session_state.pittore_fatto}.jpg",
        mime="image/jpeg"
    )

