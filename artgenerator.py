import streamlit as st
import urllib.parse
import requests
import random
from fpdf import FPDF 
import os
import time
import re # Necessario per pulire il testo dai tag HTML/Markdown

# Prova a leggere automaticamente la chiave dai Secrets di Streamlit
api_key = st.secrets.get("STABILITY_API_KEY", "")

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

# --- Funzione di Analisi Critica (IA Testuale) CORRETTA ---
def genera_analisi_ia(pittore, soggetto, api_key):
    prompt_testo = (
        f"Agisci come un critico d'arte accademico e professionale. "
        f"Scrivi una recensione tecnica e sensata di circa 250 parole in italiano "
        f"sull'opera '{soggetto}' immaginata nello stile di {pittore}. "
        f"REGOLE FONDAMENTALI: "
        f"1. Usa un vocabolario artistico reale e corretto (composizione, luce, pennellate, cromatismo). "
        f"2. NON inventare neologismi, NON usare parole inesistenti o senza senso. "
        f"3. Non divagare con concetti filosofici astrusi. Mantieni il testo ancorato alla descrizione visiva."
    )
    
    # Rimosso '?key=' dall'URL per il testo
    url_testo = f"https://text.pollinations.ai/{urllib.parse.quote(prompt_testo)}?model=openai"
    
    # La chiave per la parte testuale va passata come Bearer Token negli Headers
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    
    try:
        res = requests.get(url_testo, headers=headers, timeout=30)
        if res.status_code == 200:
            testo = res.text
            # Pulizia caratteri speciali per evitare crash FPDF
            testo = testo.replace('\xa0', ' ').replace('\u202f', ' ').replace('\u200b', '')
            testo = testo.replace('’', "'").replace('“', '"').replace('”', '"').replace('–', '-')
            return testo
        else:
            return f"Errore del server testuale (Codice HTTP {res.status_code}). Verifica la chiave nei Secrets."
    except Exception as e:
        return f"Errore di connessione API Testuale: {e}"

def crea_pdf_completo(pittore, soggetto, immagine_bytes, api_key):
    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # --- PAGINA 1: ANALISI DEL CRITICO ---
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, f"Dossier Critico: {soggetto}", 0, 1, 'L')
    pdf.set_font("Arial", 'I', 14)
    pdf.cell(0, 10, f"Nello stile di {pittore}", 0, 1, 'L')
    pdf.ln(10)
    
    testo_analisi = genera_analisi_ia(pittore, soggetto, api_key)
    
    # Pulizia definitiva per FPDF
    testo_pulito = re.sub(r'<[^>]+>', '', testo_analisi) 
    testo_per_pdf = testo_pulito.encode('latin-1', 'replace').decode('latin-1')
    
    pdf.set_font("Arial", size=11)
    pdf.multi_cell(0, 8, txt=testo_per_pdf)

    # --- PAGINA 2: L'OPERA ---
    if immagine_bytes:
        pdf.add_page(orientation='L') 
        temp_img_path = "temp_pdf_image.jpg"
        with open(temp_img_path, "wb") as f:
            f.write(immagine_bytes)
        
        pdf.image(temp_img_path, x=15, y=20, w=260) 
        
        try:
            os.remove(temp_img_path)
        except:
            pass
    
    return pdf.output(dest='S').encode('latin-1')

# --- Configurazione Base ---
st.set_page_config(page_title="Il Pennello del Tempo", page_icon="🎨", layout="wide")

try:
    st.image("banner3.png")
except:
    st.warning("Banner non trovato. Assicurati che 'banner3.png' sia nella cartella del progetto.")

# Blocco di sicurezza globale per i Secrets
if not api_key:
    st.error("⚠️ Errore: STABILITY_API_KEY non trovata nei Secrets di Streamlit! Configurala nella dashboard di Streamlit Cloud o nel file locale `.streamlit/secrets.toml`.")
    st.stop()

# --- Inizializzazione dello Stato della Sessione ---
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

        with st.spinner(f"Il maestro {pittore} sta dipingendo e scrivendo l'analisi..."):
                               
            prompt_artistico = (
                f"An entirely original masterpiece depicting '{soggetto}', "
                f"imagined and executed in the unmistakable artistic style of {pittore}. "
                f"The artwork must faithfully reproduce {pittore}'s signature visual language, "
                f"including characteristic brushwork, color palette, lighting, textures, "
                f"composition, perspective, emotional atmosphere, recurring motifs, and artistic philosophy. "
                f"The subject '{soggetto}' must be completely transformed through the artistic vision of {pittore}, "
                f"as though it were a genuine lost work from the painter’s most iconic creative period. "
                f"Authentic fine art aesthetic, museum-quality composition, expressive painterly detail, "
                f"masterful texture rendering, highly cohesive visual storytelling, "
                f"ultra detailed, cinematic lighting, 8k, masterpiece."
            )            
            prompt_encoded = urllib.parse.quote(prompt_artistico)
            seed = random.randint(1, 999999)
            
            # Endpoint Immagine (qui il parametro ?key= funziona regolarmente)
            image_url = f"https://gen.pollinations.ai/image/{prompt_encoded}?width=1024&height=768&nologo=true&seed={seed}&key={api_key}"
            
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
                else:
                    st.error(f"Errore restituito dal server Pollinations (Codice: {response.status_code}). Verifica l'API Key.")
            except Exception as e:
                st.error(f"Errore di connessione: {e}")
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
            label="🖼️ Download Image (JPG)",
            data=st.session_state.immagine_fatta,
            file_name=f"{st.session_state.soggetto_fatto}_{st.session_state.pittore_fatto}.jpg",
            mime="image/jpeg"
        )
        
    with col_dl2:
        pdf_data = crea_pdf_completo(
            st.session_state.pittore_fatto,
            st.session_state.soggetto_fatto,
            st.session_state.immagine_fatta,
            api_key
        )
        
        st.download_button(
            label="📄 Scarica Dossier PDF",
            data=pdf_data,
            file_name=f"Dossier_{st.session_state.pittore_fatto}.pdf",
            mime="application/pdf"
        )
