import streamlit as st
import urllib.parse
import requests
import random
from fpdf import FPDF 
import os
import time 
from google import genai          # NUOVO IMPORT
from google.genai import types    # NUOVO IMPORT

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
    prompt_testo = (
        f"Agisci come un critico d'arte. Scrivi una recensione tecnica di 400 parole in italiano "
        f"sull'opera '{soggetto}' realizzata da {pittore}. "
        f"IMPORTANTE: L'opera rappresenta solo ed esclusivamente '{soggetto}'. "
        f"Non menzionare altri soggetti tipici dell'autore (come ballerine, gigli o cavalli) "
        f"se non sono il soggetto richiesto. Concentrati sulla tecnica e sulla filosofia dello stile."
    )
    
    url_testo = f"https://text.pollinations.ai/{urllib.parse.quote(prompt_testo)}?model=openai"
    
    try:
        res = requests.get(url_testo, timeout=30)
        if res.status_code == 200:
            testo = res.text
            testo = testo.replace('\xa0', ' ').replace('\u202f', ' ').replace('\u200b', '')
            testo = testo.replace('’', "'").replace('“', '"').replace('”', '"').replace('–', '-')
            return testo
    except Exception:
        pass
    return f"Analisi dell'opera '{soggetto}' nello stile di {pittore}."
    
def crea_pdf_completo(pittore, soggetto, immagine_bytes):
    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, f"Dossier: {soggetto.capitalize()} del maestro {pittore}", 0, 1, 'L')
    pdf.set_font("Arial", 'I', 14)
    pdf.cell(0, 10, f"Stile: {pittore}", 0, 1, 'L')
    pdf.ln(10)

    with st.spinner("Il critico d'arte sta scrivendo..."):
        testo_analisi = genera_analisi_ia(pittore, soggetto)
    
    import re
    testo_pulito = re.sub(r'<[^>]+>', '', testo_analisi) 
    
    testo_per_pdf = testo_pulito.encode('latin-1', 'replace').decode('latin-1').replace('?', '')
        
    pdf.set_font("Arial", size=11)
    pdf.multi_cell(0, 8, txt=testo_per_pdf)

    if immagine_bytes:
        pdf.add_page(orientation='L') 
        temp_img = f"temp_{random.randint(1,999)}.jpg"
        with open(temp_img, "wb") as f:
            f.write(immagine_bytes)
        
        pdf.image(temp_img, x=25, y=20, w=245) 
        os.remove(temp_img)
    
    return pdf.output(dest='S').encode('latin-1')

# --- Configurazione Base ---
st.set_page_config(page_title="Il Pennello del Tempo", page_icon="🎨", layout="wide")

try:
    st.image("banner3.png")
except:
    st.warning("Banner non trovato. Assicurati che 'banner3.png' sia nella cartella del progetto.")

# --- CAMPO PER INSERIMENTO API KEY NELLA SIDEBAR ---
#st.sidebar.header("🔑 Configurazione API")
#st.sidebar.markdown("Per generare le immagini, inserisci la tua chiave di Google AI Studio.")
#api_key_input = st.sidebar.text_input("API Key di Google", type="password")
#genai.configure(api_key=st.secrets["API_KEY"])


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
    # Recuperiamo la chiave dai Secrets di Streamlit invece che dall'input
    try:
        api_key_fissa = st.secrets["API_KEY"]
    except:
        st.error("🔑 Chiave API non trovata nei Secrets di Streamlit!")
        st.stop()
        
    if pittore and soggetto:
        st.session_state.immagine_fatta = None 

        with st.spinner(f"Il maestro {pittore} sta dipingendo..."):
            prompt_artistico = (
                f"A centered, symmetrical professional masterpiece depicting ONLY '{soggetto}' as the absolute main focus. "
                f"The subject '{soggetto}' is placed in the dead center of the frame. "
                f"Style: exact recreation of {pittore}'s unique visual language. "
                f"Strictly avoid any typical subjects of {pittore} that are not '{soggetto}' (no dancers, no unintended figures). "
                f"Use the authentic historical medium, color palette, and surface texture specific to {pittore}. "
                f"Museum quality, 8k resolution, perfectly composed, focused on '{soggetto}'."
            )
            
            try:
                # Inizializza il client con la chiave dai Secrets
                client = genai.Client(api_key=api_key_fissa)
                
                # Usa 'imagen-3.0-generate-001' o 'imagen-3.0-fast-001'
                # Imagen 2.0 è spesso deprecato o limitato ad account enterprise
                response = client.models.generate_images(
                    model='imagen-2.5', 
                    prompt=prompt_artistico,
                    config=types.GenerateImagesConfig(
                        number_of_images=1,
                        output_mime_type="image/jpeg",
                        aspect_ratio="4:3",
                        safety_filter_level="BLOCK_ONLY_HIGH", # Meno restrittivo per l'arte storica
                        person_generation="ALLOW_ADULT"
                    )
                )
                
                # Estrazione dei Bytes dell'immagine
                if response.generated_images:
                    image_bytes = response.generated_images[0].image.image_bytes
                    
                    st.session_state.immagine_fatta = image_bytes
                    st.session_state.pittore_fatto = pittore
                    st.session_state.soggetto_fatto = soggetto
                    
                    # --- LOGICA DEL TIMER ---
                    placeholder = st.empty()
                    for seconds in range(10, 0, -1):
                        placeholder.warning(f"⏳ Pronto per una nuova opera tra {seconds} secondi.")
                        time.sleep(1)
                    placeholder.success("✅ Pronto per una nuova generazione!")
                    
                    st.rerun() 
                else:
                    st.error("Il modello non ha restituito alcuna immagine. Riprova con un altro prompt.")
                    
            except Exception as e:
                st.error(f"Errore di connessione con l'API Google: {e}")
    else:
        st.warning("Inserisci entrambi i campi.")

# --- MOSTRA L'IMMAGINE E I PULSANTI DOWNLOAD ---
if st.session_state.immagine_fatta is not None:
    st.image(st.session_state.immagine_fatta, 
             caption=f"{st.session_state.soggetto_fatto} in stile {st.session_state.pittore_fatto}", 
             use_container_width=True)
    
    st.success("Opera completata!")
    
    col_dl1, col_dl2 = st.columns(2)
    
    with col_dl1:
        st.download_button(
            label="🖼️ Scarica solo l'Immagine (JPG)",
            data=st.session_state.immagine_fatta,
            file_name=f"Soggetto_{st.session_state.soggetto_fatto}_dal_maestro_{st.session_state.pittore_fatto}.jpg",
            mime="image/jpeg"
        )
        
    #with col_dl2:
        # Generazione e Bottone Download PDF
        #pdf_data = crea_pdf_completo(
            #st.session_state.pittore_fatto,
            #st.session_state.soggetto_fatto,
            #st.session_state.immagine_fatta
        #)
        
        #st.download_button(
            #label="📄 Scarica Dossier PDF",
            #data=pdf_data,
            #file_name=f"Recensione_critica_di_{st.session_state.soggetto_fatto}_del_maestro_{st.session_state.pittore_fatto}.pdf",
            #mime="application/pdf"
        #)
