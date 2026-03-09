import streamlit as st
from fpdf import FPDF
import io 
import os
import requests
import time

# --- Configurazione API ---
HF_API_KEY = st.secrets["HF_API_KEY"]

def genera_analisi_robusta(pittore, soggetto):
    """Prova Hugging Face, se fallisce passa a Gemini."""
    # 1. TENTATIVO HUGGING FACE
    try:
        api_url = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
        headers = {"Authorization": f"Bearer {HF_API_KEY}"}
        prompt = f"<s>[INST] Sei un critico d'arte. Analizza in italiano lo stile di {pittore} su '{soggetto}'. [/INST]"
        response = requests.post(api_url, headers=headers, json={"inputs": prompt}, timeout=10)
        if response.status_code == 200:
            return response.json()[0]['generated_text'].split("[/INST]")[-1].strip()
    except:
        pass

    # 2. TENTATIVO GEMINI (Fallback per errore 429)
    try:
        import google.generativeai as genai
        genai.configure(api_key=st.secrets["API_KEY"])
        model = genai.GenerativeModel('gemini-1.5-flash') 
        response = model.generate_content(f"Analizza brevemente '{soggetto}' nello stile di {pittore}.")
        return response.text
    except:
        return f"Un'interessante interpretazione di {soggetto} attraverso gli occhi di {pittore}."

def genera_immagine_huggingface(pittore, soggetto):
    """Genera l'immagine con gestione degli errori."""
    # Usiamo l'URL corretto richiesto da HF
    api_url = "https://router.huggingface.co/hf-inference/models/stabilityai/stable-diffusion-xl-base-1.0"
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    prompt = f"A masterpiece oil painting of {soggetto} in the style of {pittore}, detailed."
    
    for _ in range(3):
        try:
            response = requests.post(api_url, headers=headers, json={"inputs": prompt}, timeout=30)
            if response.status_code == 200:
                return response.content
            time.sleep(5)
        except:
            continue
    return None

# --- PDF ---
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'IL PENNELLO DEL TEMPO', 0, 1, 'C')

def crea_pdf(pittore, soggetto, analisi, img_bytes):
    pdf = PDF()
    
    # --- PAGINA 1: ANALISI (Verticale) ---
    pdf.add_page() # Default è 'P' (Portrait)
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, f"Soggetto: {soggetto} nello stile di {pittore}", 0, 1, 'L')
    pdf.ln(5)
    
    pdf.set_font("Arial", size=12)
    # Pulizia testo per PDF (evita errori caratteri speciali)
    testo_pulito = analisi.encode('latin-1', 'replace').decode('latin-1')
    # Usiamo multi_cell per mandare a capo il testo automaticamente
    pdf.multi_cell(0, 10, txt=testo_pulito)

    # --- PAGINA 2: IMMAGINE (Orizzontale - Landscape) ---
    if img_bytes:
        # Aggiungiamo una nuova pagina specificando orientamento Orizzontale ('L')
        # Una pagina A4 in orizzontale è larga circa 297mm e alta 210mm
        pdf.add_page(orientation='L')
        
        # Salviamo l'immagine temporaneamente per FPDF
        # Usiamo .jpg perché Hugging Face restituisce spesso JPEG
        with open("temp_image.jpg", "wb") as f:
            f.write(img_bytes)
        
        # Inseriamo l'immagine adattandola alla larghezza della pagina
        # x=10, y=10 sono i margini superiore e sinistro (in mm)
        # w=277 calcola la larghezza disponibile (297mm totale - 20mm di margini)
        # L'altezza verrà calcolata automaticamente mantenendo le proporzioni
        try:
            pdf.image("temp_image.jpg", x=10, y=10, w=277) 
        except Exception as e:
            st.error(f"Errore inserimento immagine nel PDF: {e}")
        finally:
            # Rimuoviamo sempre il file temporaneo
            if os.path.exists("temp_image.jpg"):
                os.remove("temp_image.jpg")
    
    # Restituiamo i dati del PDF come bytes
    return pdf.output(dest='S').encode('latin-1')

# --- UI ---
st.set_page_config(page_title="Il Pennello del Tempo", layout="wide")
st.image("banner.png")
st.title("🎨 Il Pennello del Tempo")

if 'res' not in st.session_state: st.session_state.res = None

c1, c2 = st.columns(2)
p_in = c1.text_input("Artista")
s_in = c2.text_input("Soggetto")

if st.button("Genera Visione Artistica"):
    if p_in and s_in:
        with st.spinner("Creazione in corso..."):
            # CHIAMATA CORRETTA: usa genera_analisi_robusta
            analisi_testo = genera_analisi_robusta(p_in, s_in)
            immagine_dati = genera_immagine_huggingface(p_in, s_in)
            
            if immagine_dati:
                st.session_state.res = {
                    "t": analisi_testo, 
                    "i": immagine_dati, 
                    "p": p_in, 
                    "s": s_in
                }
            else:
                st.error("Errore generazione immagine. Riprova.")

if st.session_state.res:
    r = st.session_state.res
    st.info(r["t"])
    st.image(r["i"], use_container_width=True)
    
    pdf_file = crea_pdf(r["p"], r["s"], r["t"], r["i"])
    st.download_button("💾 Scarica PDF", data=pdf_file, file_name=f"{r['p']}.pdf")
