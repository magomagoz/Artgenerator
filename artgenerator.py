import streamlit as st
from fpdf import FPDF
import os
import requests
import time

HF_API_KEY = st.secrets["HF_API_KEY"]

def genera_analisi_robusta(pittore, soggetto):
    """Genera una recensione d'arte profonda e strutturata."""
    prompt_discorsivo = (
        f"Scrivi una recensione d'arte critica, colta e molto lunga (circa 600 parole) su come {pittore} "
        f"rappresenterebbe il soggetto '{soggetto}'. La recensione deve essere strutturata con: "
        f"1. Analisi Tecnica (uso della luce, pennellate, tavolozza colori). "
        f"2. Composizione (gestione dello spazio, equilibrio visivo, ritmo). "
        f"3. Interpretazione Concettuale (la filosofia estetica dietro l'opera). "
        f"Usa un tono ricercato e descrittivo, tipico di un esperto di storia dell'arte."
    )
    
    # Tentativo Hugging Face
    try:
        api_url = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
        headers = {"Authorization": f"Bearer {HF_API_KEY}"}
        payload = {
            "inputs": f"<s>[INST] {prompt_discorsivo} [/INST]",
            "parameters": {"max_new_tokens": 1000, "temperature": 0.7}
        }
        response = requests.post(api_url, headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            return response.json()[0]['generated_text'].split("[/INST]")[-1].strip()
    except:
        pass
    
    # Fallback Gemini
    try:
        import google.generativeai as genai
        genai.configure(api_key=st.secrets["API_KEY"])
        model = genai.GenerativeModel('gemini-1.5-flash')
        return model.generate_content(prompt_discorsivo).text
    except:
        return f"Interpretazione di {soggetto} nello stile di {pittore}: un'opera che fonde luce e colore in una visione magistrale."

def genera_immagine_huggingface(pittore, soggetto):
    """Richiede un formato orizzontale specifico."""
    api_url = "https://router.huggingface.co/hf-inference/models/stabilityai/stable-diffusion-xl-base-1.0"
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    # Prompt ottimizzato per formato landscape
    prompt_img = (
        f"Professional wide-angle oil painting of {soggetto} in the style of {pittore}, "
        f"high-end artistic quality, masterful brushwork, lighting and texture. "
        f"Landscape composition, wide aspect ratio 1.42:1."
    )
    
    for _ in range(3):
        try:
            response = requests.post(api_url, headers=headers, json={"inputs": prompt_img}, timeout=40)
            if response.status_code == 200: return response.content
            time.sleep(5)
        except: continue
    return None

# --- PDF con Layout 40x28 ---
def crea_pdf(pittore, soggetto, analisi, img_bytes):
    # Formato personalizzato 400x280 mm
    pdf = FPDF(unit='mm', format=(400, 280))
    pdf.add_page()
    
    # Testo
    pdf.set_font("Arial", 'B', 20)
    pdf.cell(0, 15, f"{soggetto} - Stile: {pittore}", 0, 1, 'C')
    pdf.ln(10)
    pdf.set_font("Arial", size=14)
    testo = analisi.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 10, txt=testo)
    
    # Immagine
    if img_bytes:
        pdf.add_page()
        with open("temp.jpg", "wb") as f: f.write(img_bytes)
        pdf.image("temp.jpg", x=20, y=20, w=360) # 400 - 40 di margine
        os.remove("temp.jpg")
        
    return pdf.output(dest='S').encode('latin-1')

# --- UI ---
st.set_page_config(page_title="Il Pennello del Tempo", layout="wide")
st.title("🎨 Il Pennello del Tempo - Edizione Professionale")

if 'res' not in st.session_state: st.session_state.res = None

col1, col2 = st.columns(2)
p_in = col1.text_input("Artista")
s_in = col2.text_input("Soggetto")

if st.button("Genera Visione Artistica"):
    if p_in and s_in:
        # Inizializziamo il contenitore dei risultati
        st.session_state.res = {"t": None, "i": None, "p": p_in, "s": s_in}
        
        # 1. Generazione Testo (Indipendente)
        with st.spinner("Il critico sta studiando l'opera..."):
            st.session_state.res["t"] = genera_analisi_robusta(p_in, s_in)
            
        # 2. Generazione Immagine (Indipendente)
        with st.spinner("Il pittore è al lavoro..."):
            img = genera_immagine_huggingface(p_in, s_in)
            if img:
                st.session_state.res["i"] = img
            else:
                st.warning("L'immagine non è stata generata per sovraccarico. Il testo è comunque pronto.")
    else:
        st.warning("Inserisci entrambi i campi!")

if st.session_state.res:
    st.info(st.session_state.res["t"])
    st.image(st.session_state.res["i"], use_container_width=True)
    pdf = crea_pdf(st.session_state.res["p"], st.session_state.res["s"], st.session_state.res["t"], st.session_state.res["i"])
    st.download_button("💾 Scarica Dossier (Formato 40x28cm)", data=pdf, file_name="opera.pdf")
