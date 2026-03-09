import streamlit as st
from fpdf import FPDF
import io 
import os
import requests

# --- Configurazione API ---
# Assicurati di avere HF_API_KEY nei Secrets di Streamlit
HF_API_KEY = st.secrets["HF_API_KEY"]

def chiama_huggingface_testo(prompt):
    """Genera l'analisi testuale usando un modello LLM su Hugging Face."""
    api_url = "https://router.huggingface.co/hf-inference/models/mistralai/Mistral-7B-Instruct-v0.3"
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    payload = {
        "inputs": f"<s>[INST] {prompt} [/INST]",
        "parameters": {"max_new_tokens": 500, "temperature": 0.7}
    }
    response = requests.post(api_url, headers=headers, json=payload)
    if response.status_code == 200:
        return response.json()[0]['generated_text'].split("[/INST]")[-1].strip()
    else:
        return "Analisi non disponibile al momento."

def genera_immagine_huggingface(prompt):
    """Genera l'immagine usando Stable Diffusion XL."""
    api_url = "https://router.huggingface.co/hf-inference/models/stabilityai/stable-diffusion-xl-base-1.0"
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    payload = {"inputs": prompt}
    response = requests.post(api_url, headers=headers, json=payload)
    if response.status_code == 200:
        return response.content
    else:
        raise Exception(f"Errore Immagine: {response.text}")

# --- Funzione PDF (già corretta per .jpg) ---
class PDF(FPDF):
    def header(self):
        if self.page_no() == 1:
            self.set_font('Arial', 'B', 24)
            self.cell(0, 20, 'IL PENNELLO DEL TEMPO', 0, 1, 'C')
            self.ln(10)

def crea_pdf_completo(pittore, soggetto, testo_analisi, immagine_bytes):
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, f"Soggetto: {soggetto} nello stile di {pittore}", 0, 1, 'L')
    pdf.ln(5)
    pdf.set_font("Arial", size=12)
    testo_pulito = testo_analisi.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 10, txt=testo_pulito)

    if immagine_bytes:
        pdf.add_page(orientation='L')
        with open("temp_image.jpg", "wb") as f:
            f.write(immagine_bytes)
        pdf.image("temp_image.jpg", x=10, y=10, w=277) 
        os.remove("temp_image.jpg")
    
    return pdf.output(dest='S').encode('latin-1')

# --- UI Streamlit ---
st.set_page_config(page_title="Il Pennello del Tempo", page_icon="🎨", layout="wide")
if os.path.exists("banner.png"):
    st.image("banner.png")

st.title("🎨 Il Pennello del Tempo: Analisi & Creazione")

# Inizializzazione Session State
for key in ['analisi_generata', 'immagine_generata', 'pittore_corrente', 'soggetto_corrente']:
    if key not in st.session_state: st.session_state[key] = None

col1, col2 = st.columns(2)
pittore = col1.text_input("Scegli un Pittore")
soggetto = col2.text_input("Soggetto da interpretare")

if st.button("Genera Interpretazione Artistica"):
    if pittore and soggetto:
        # 1. ANALISI TESTUALE (Hugging Face)
        with st.spinner('Il critico d\'arte sta scrivendo...'):
            prompt_testo = f"Sei un esperto d'arte. Analizza il soggetto '{soggetto}' come se fosse dipinto da {pittore}. Parla di tecnica, colori e significato in italiano."
            analisi = chiama_huggingface_testo(prompt_testo)
            st.session_state.analisi_generata = analisi
            st.session_state.pittore_corrente = pittore
            st.session_state.soggetto_corrente = soggetto

        # 2. IMMAGINE (Hugging Face)
        with st.spinner('Il maestro sta dipingendo...'):
            try:
                prompt_img = f"A professional oil painting of {soggetto} in the style of {pittore}, masterpiece, highly detailed."
                img_bytes = genera_immagine_huggingface(prompt_img)
                st.session_state.immagine_generata = img_bytes
            except Exception as e:
                st.error(f"Errore Immagine: {e}")

# Visualizzazione Persistente
if st.session_state.analisi_generata:
    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🖋️ Analisi Testuale")
        st.write(st.session_state.analisi_generata)
    with c2:
        st.subheader("🖼️ Opera Generata")
        st.image(st.session_state.immagine_generata)
        
        pdf_data = crea_pdf_completo(st.session_state.pittore_corrente, st.session_state.soggetto_corrente, st.session_state.analisi_generata, st.session_state.immagine_generata)
        st.download_button("💾 Scarica PDF Artistico", data=pdf_data, file_name=f"{st.session_state.pittore_corrente}.pdf", mime="application/pdf")
