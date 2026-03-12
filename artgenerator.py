import streamlit as st
from fpdf import FPDF
import io 
import os
import requests
import time

# --- Configurazione API ---
HF_API_KEY = st.secrets["HF_API_KEY"]

def genera_analisi_robusta(pittore, soggetto):
    """Prova Hugging Face, se fallisce passa a Gemini con prompt discorsivi."""
    
    prompt_discorsivo = f"Sei un critico d'arte colto e raffinato. Scrivi un'analisi discorsiva in italiano immaginando come {pittore} interpreterebbe il soggetto '{soggetto}'. Soffermati in modo dettagliato sulla gestione della luce, sull'uso dei colori e sulla tecnica tipica delle sue pennellate, descrivendo l'atmosfera immersiva dell'opera."
    
    # 1. TENTATIVO HUGGING FACE
    try:
        api_url = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
        headers = {"Authorization": f"Bearer {st.secrets['HF_API_KEY']}"}
        prompt_hf = f"<s>[INST] {prompt_discorsivo} [/INST]"
        
        # CORREZIONE: Ho reinserito i parametri per la lunghezza del testo!
        payload = {
            "inputs": prompt_hf,
            "parameters": {
                "max_new_tokens": 400,
                "return_full_text": False,
                "temperature": 0.7
            }
        }
        
        response = requests.post(api_url, headers=headers, json=payload, timeout=15)
        if response.status_code == 200:
            testo = response.json()[0]['generated_text']
            # Pulizia sicura del testo
            if "[/INST]" in testo:
                testo = testo.split("[/INST]")[-1]
            return testo.strip()
    except:
        pass # Se HF fallisce, passa a Gemini

    # 2. TENTATIVO GEMINI (Fallback per errore 429)
    try:
        import google.generativeai as genai
        genai.configure(api_key=st.secrets["API_KEY"])
        model = genai.GenerativeModel('gemini-1.5-flash') 
        response = model.generate_content(prompt_discorsivo)
        if response.text:
            return response.text
    except:
        pass # Se Gemini fallisce, passa al testo di emergenza

    # 3. TESTO DI EMERGENZA (Se entrambe le AI sono bloccate)
    return f"L'opera rappresenta {soggetto} attraverso il filtro estetico inconfondibile di {pittore}. La gestione magistrale della luce e l'uso vibrante dei colori catturano perfettamente l'essenza della sua tecnica, creando un'atmosfera profondamente immersiva."

def genera_immagine_huggingface(pittore, soggetto):
    """Genera l'immagine con un prompt focalizzato su luce e stile."""
    api_url = "https://router.huggingface.co/hf-inference/models/stabilityai/stable-diffusion-xl-base-1.0"
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    
    # Prompt in inglese ottimizzato per Stable Diffusion XL (luce e tecnica)
    prompt_img = (
        f"A masterpiece painting of {soggetto} in the exact, unmistakable artistic style of {pittore}. "
        f"Focus heavily on the signature dramatic lighting, authentic atmospheric color palette, "
        f"and specific brushwork typical of {pittore}'s iconic artworks. "
        f"Highly detailed, aesthetic, museum quality composition."
    )
    
    for _ in range(3):
        try:
            response = requests.post(api_url, headers=headers, json={"inputs": prompt_img}, timeout=30)
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
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, f"Soggetto: {soggetto} - Stile: {pittore}", 0, 1, 'L')
    pdf.ln(5)
    pdf.set_font("Arial", size=12)
    testo_pulito = analisi.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 10, txt=testo_pulito)

    # --- PAGINA 2: IMMAGINE (Orizzontale con controllo altezza) ---
    if img_bytes:
        pdf.add_page(orientation='L')
        
        with open("temp_print.jpg", "wb") as f:
            f.write(img_bytes)
        
        # Limitiamo l'altezza massima per evitare tagli a fondo pagina
        altezza_max = 180 
        
        try:
            # Usando 'h=altezza_max' e omettendo 'w', l'immagine si rimpicciolisce 
            # proporzionalmente finché non sta tutta nella pagina.
            pdf.image("temp_print.jpg", x=10, y=15, h=altezza_max) 
            
        except Exception as e:
            st.error(f"Errore PDF: {e}")
        finally:
            if os.path.exists("temp_print.jpg"):
                os.remove("temp_print.jpg")
    
    return pdf.output(dest='S').encode('latin-1')

# --- UI ---
st.set_page_config(page_title="Il Pennello del Tempo", layout="wide")

# Controllo se il banner esiste prima di caricarlo per evitare errori
if os.path.exists("banner.png"):
    st.image("banner.png")

st.title("🎨 Il Pennello del Tempo")

if 'res' not in st.session_state: st.session_state.res = None

c1, c2 = st.columns(2)
p_in = c1.text_input("Artista")
s_in = c2.text_input("Soggetto")

if st.button("Genera Visione Artistica"):
    if p_in and s_in:
        with st.spinner("Creazione in corso..."):
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
