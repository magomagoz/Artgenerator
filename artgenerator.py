import streamlit as st
import urllib.parse
import requests
import random
from fpdf import FPDF 
import os
import time
import re # Necessario per pulire il testo dai tag HTML/Markdown

# Recupero unico dell'API Key dai Secrets
api_key = st.secrets.get("STABILITY_API_KEY", "")

# --- Funzione PDF Avanzata (Adattata per Immagine/Titolo) ---
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

def interroga_specifiche_pittore(pittore, api_key):
    """
    Chiede all'IA in background quali sono le caratteristiche visive chiave del pittore
    per usarle dinamicamente nel prompt dell'immagine.
    """
    prompt_ricerca = (
        f"Analyze the unique artistic style of '{pittore}'. "
        f"Provide a short, dense list of 3 to 5 key visual elements, materials, medium, "
        f"and compositional rules that define their work (e.g., for Arcimboldo: 'composed of fruits and vegetables', "
        f"for Van Gogh: 'thick impasto, swirling brushstrokes', for Monet: 'broken color, dappled light'). "
        f"Respond ONLY with the English keywords, separated by commas, no full sentences."
    )
    
    url_testo = "https://text.pollinations.ai/"
    payload = {
        "messages": [{"role": "user", "content": prompt_ricerca}],
        "model": "openai"
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        res = requests.post(url_testo, json=payload, headers=headers, timeout=15)
        if res.status_code == 200:
            # Ritorna la lista di specifiche pulita (es. "mannerist portrait, composed of food, oil on canvas")
            return res.text.strip().replace("\n", " ")
        return ""
    except:
        return "" # In caso di timeout o errore, restituisce vuoto senza bloccare il programma

# --- Funzione di Analisi Critica (IA Testuale tramite POST) ---
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
    
    # Endpoint ufficiale per richieste strutturate
    url_testo = "https://text.pollinations.ai/"
    
    payload = {
        "messages": [
            {"role": "user", "content": prompt_testo}
        ],
        "model": "openai"
    }
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        res = requests.post(url_testo, json=payload, headers=headers, timeout=30)
        if res.status_code == 200:
            testo = res.text
            # Pulizia caratteri speciali per evitare crash FPDF
            testo = testo.replace('\xa0', ' ').replace('\u202f', ' ').replace('\u200b', '')
            testo = testo.replace('’', "'").replace('“', '"').replace('”', '"').replace('–', '-')
            return testo
        else:
            return f"Errore del server durante la generazione del testo (Codice HTTP {res.status_code})."
    except Exception as e:
        return f"Errore di connessione API Testuale: {e}"

# --- Creazione del PDF utilizzando il testo già salvato in memoria ---
def crea_pdf_completo(pittore, soggetto, immagine_bytes, testo_analisi):
    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # --- PAGINA 1: ANALISI DEL CRITICO ---
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, f"Dossier Critico: {soggetto}", 0, 1, 'L')
    pdf.set_font("Arial", 'I', 14)
    pdf.cell(0, 10, f"Nello stile di {pittore}", 0, 1, 'L')
    pdf.ln(10)
    
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

# Controllo bloccante per la chiave API
if not api_key:
    st.error("⚠️ Errore: STABILITY_API_KEY non trovata nei Secrets di Streamlit! Configurala nella dashboard di Streamlit Cloud o nel file locale `.streamlit/secrets.toml`.")
    st.stop()

# --- Inizializzazione Unica dello Stato della Sessione ---
if 'immagine_fatta' not in st.session_state:
    st.session_state.immagine_fatta = None
if 'pittore_fatto' not in st.session_state:
    st.session_state.pittore_fatto = ""
if 'soggetto_fatto' not in st.session_state:
    st.session_state.soggetto_fatto = ""
if 'testo_fatto' not in st.session_state:
    st.session_state.testo_fatto = ""

# --- Input Utente ---
col1, col2 = st.columns(2)
pittore = col1.text_input("🎨 Nome completo del Pittore (movimento artistico e/o tecnica specifica)")
soggetto = col2.text_input("Soggetto da dipingere")

if st.button("Genera Visione Artistica"):
    if pittore and soggetto:
        st.session_state.immagine_fatta = None 
        st.session_state.testo_fatto = ""

        with st.spinner(f"Studio del maestro {pittore} in corso e preparazione della tela..."):
            
            # --- FASE 1: INTERROGAZIONE IN BACKGROUND (DNA DEL PITTORE) ---
            specifiche_pittore = interroga_specifiche_pittore(pittore, api_key)
            
            # Se l'IA ha risposto, iniettiamo le specifiche, altrimenti lasciamo vuoto
            aiuto_stile = f", embodying: {specifiche_pittore}," if specifiche_pittore else ""
            
            # --- FASE 2: COMPOSIZIONE PROMPT UNIVERSALE DINAMICO ---
            prompt_artistico = (
                f"A masterwork painting depicting '{soggetto}' inside the world and unique vision of {pittore}{aiuto_stile}. "
                f"The image must encapsulate the profound essence of {pittore}'s art: from the authentic physical medium "
                f"to the historical technique, surface texture, and period-accurate color theory. "
                f"The subject '{soggetto}' is completely reinterpreted through the painter's core creative philosophy and compositional logic, "
                f"as a genuine piece from their era. Fine art aesthetic, museum exhibition quality, free of digital rendering artifacts."
            )            
            
            prompt_encoded = urllib.parse.quote(prompt_artistico)
            seed = random.randint(1, 999999)
            
            image_url = f"https://gen.pollinations.ai/image/{prompt_encoded}?width=1024&height=768&nologo=true&seed={seed}&key={api_key}"
            
            try:
                # --- FASE 3: GENERAZIONE IMMAGINE ---
                response = requests.get(image_url, timeout=45) 
                
                if response.status_code == 200:
                    # --- FASE 4: GENERAZIONE TESTO CRITICO ---
                    testo_critico = genera_analisi_ia(pittore, soggetto, api_key)
                    
                    # Salva tutto nello stato contemporaneamente
                    st.session_state.immagine_fatta = response.content
                    st.session_state.pittore_fatto = pittore
                    st.session_state.soggetto_fatto = soggetto
                    st.session_state.testo_fatto = testo_critico
                    
                    # --- LOGICA DEL TIMER ---
                    placeholder = st.empty()
                    for seconds in range(10, 0, -1):
                        placeholder.warning(f"⏳ Pronto per una nuova opera tra {seconds} secondi.")
                        time.sleep(1)
                    placeholder.success("✅ Pronto per una nuova generazione!")
                    
                    st.rerun() 
                else:
                    st.error(f"Errore restituito dal server Pollinations Immagine (Codice: {response.status_code}).")
            except Exception as e:
                st.error(f"Errore di connessione o timeout: {e}")
    else:
        st.warning("Inserisci entrambi i campi.")
                    
                    # Salva tutto nello stato contemporaneamente
                    st.session_state.immagine_fatta = response.content
                    st.session_state.pittore_fatto = pittore
                    st.session_state.soggetto_fatto = soggetto
                    st.session_state.testo_fatto = testo_critico
                    
                    # --- LOGICA DEL TIMER ---
                    placeholder = st.empty()
                    for seconds in range(10, 0, -1):
                        placeholder.warning(f"⏳ Pronto per una nuova opera tra {seconds} secondi.")
                        time.sleep(1)
                    placeholder.success("✅ Pronto per una nuova generazione!")
                    
                    st.rerun() 
                else:
                    st.error(f"Errore restituito dal server Pollinations Immagine (Codice: {response.status_code}). Verifica l'API Key.")
            except Exception as e:
                st.error(f"Errore di connessione: L'API ci ha messo troppo tempo a rispondere. {e}")
    else:
        st.warning("Inserisci entrambi i campi.")

# --- MOSTRA L'IMMAGINE E I PULSANTI DOWNLOAD ---
if st.session_state.immagine_fatta is not None:
    st.image(st.session_state.immagine_fatta, 
             caption=f"{st.session_state.soggetto_fatto} in stile {st.session_state.pittore_fatto}", 
             use_container_width=True)
    
    st.success("Opera completata!")
    
    col_dl1, col_dl2 = st.columns(2)
    
    #with col_dl1:
    st.download_button(
        label="🖼️ Download Image (JPG)",
        data=st.session_state.immagine_fatta,
        file_name=f"{st.session_state.soggetto_fatto}_{st.session_state.pittore_fatto}.jpg",
        mime="image/jpeg"
    )
        
    #with col_dl2:
        # Ora passiamo direttamente st.session_state.testo_fatto, istantaneo e senza nuove chiamate API
        #pdf_data = crea_pdf_completo(
            #st.session_state.pittore_fatto,
            #st.session_state.soggetto_fatto,
            #st.session_state.immagine_fatta,
            #st.session_state.testo_fatto
        #)
        
        #st.download_button(
            #label="📄 Scarica Dossier PDF",
            #data=pdf_data,
            #file_name=f"Dossier_{st.session_state.pittore_fatto}.pdf",
            #mime="application/pdf"
        #)
