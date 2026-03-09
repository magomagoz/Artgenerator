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
    
    # --- TENTATIVO 1: HUGGING FACE (Mistral) ---
    try:
        api_url = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
        headers = {"Authorization": f"Bearer {st.secrets['HF_API_KEY']}"}
        prompt = f"<s>[INST] Sei un critico d'arte. Analizza in italiano lo stile di {pittore} su '{soggetto}'. [/INST]"
        
        response = requests.post(api_url, headers=headers, json={"inputs": prompt}, timeout=10)
        if response.status_code == 200:
            return response.json()[0]['generated_text'].split("[/INST]")[-1].strip()
    except:
        pass # Se HF fallisce, non fare nulla e passa oltre

    # --- TENTATIVO 2: GEMINI (Google) ---
    try:
        import google.generativeai as genai
        genai.configure(api_key=st.secrets["API_KEY"])
        # Usiamo 2.5 o 1.5 a seconda di quale hai verificato funzionante
        model = genai.GenerativeModel('gemini-1.5-flash') 
        prompt = f"Analizza brevemente '{soggetto}' nello stile di {pittore}."
        response = model.generate_content(prompt)
        return response.text
    except:
        pass

    # --- TENTATIVO 3: RISPOSTA DI EMERGENZA (Senza AI) ---
    return f"L'opera rappresenta {soggetto} attraverso il filtro estetico unico di {pittore}, con particolare attenzione alla forma e al colore."


def genera_immagine_huggingface(pittore, soggetto):
    """Genera l'immagine con tentativi automatici in caso di server occupato."""
    api_url = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    prompt = f"A masterpiece oil painting of {soggetto} in the exact and specific style of {pittore}, detailed texture."
    
    # Sistema di 'Retry' (riprova 3 volte se occupato)
    for i in range(3):
        try:
            response = requests.post(api_url, headers=headers, json={"inputs": prompt}, timeout=30)
            if response.status_code == 200:
                return response.content
            elif response.status_code == 503: # Model loading / Busy
                time.sleep(5) # Aspetta 5 secondi prima di riprovare
                continue
        except:
            pass
    
    raise Exception("I server di Hugging Face sono molto carichi. Attendi 10 secondi e premi di nuovo il tasto.")

# --- Classe PDF (JPG support) ---
class PDF(FPDF):
    def header(self):
        if self.page_no() == 1:
            self.set_font('Arial', 'B', 20)
            self.cell(0, 15, 'IL PENNELLO DEL TEMPO', 0, 1, 'C')

def crea_pdf(pittore, soggetto, analisi, img_bytes):
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, f"{soggetto} nello stile di {pittore}", 0, 1)
    pdf.set_font("Arial", size=11)
    pdf.multi_cell(0, 7, txt=analisi.encode('latin-1', 'replace').decode('latin-1'))
    
    if img_bytes:
        pdf.add_page(orientation='L')
        with open("temp.jpg", "wb") as f: f.write(img_bytes)
        pdf.image("temp.jpg", x=10, y=10, w=277)
        os.remove("temp.jpg")
    return pdf.output(dest='S').encode('latin-1')

# --- Interfaccia ---
st.set_page_config(page_title="Il Pennello del Tempo", layout="wide")
st.title("🎨 Il Pennello del Tempo")

if 'res' not in st.session_state: st.session_state.res = None

col1, col2 = st.columns(2)
p_in = col1.text_input("Artista")
s_in = col2.text_input("Soggetto")

if st.button("Genera Visione Artistica"):
    if p_in and s_in:
        with st.spinner(f"Sto chiedendo a {p_in} di dipingere..."):
            try:
                # CORREZIONE QUI: Usa il nuovo nome della funzione con cascata
                txt = genera_analisi_robusta(p_in, s_in) 
                
                img = genera_immagine_huggingface(p_in, s_in)
                st.session_state.res = {"t": txt, "i": img, "p": p_in, "s": s_in}
            except Exception as e:
                st.error(str(e))
    else:
        st.warning("Inserisci i dati.")

if st.session_state.res:
    r = st.session_state.res
    st.info(r["t"])
    st.image(r["i"], use_container_width=True)
    
    pdf = crea_pdf(r["p"], r["s"], r["t"], r["i"])
    st.download_button("💾 Scarica PDF", data=pdf, file_name=f"{r['p']}.pdf")
