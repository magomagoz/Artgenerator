import streamlit as st
from fpdf import FPDF
import io 
import os
import requests

# --- Configurazione API ---
HF_API_KEY = st.secrets["HF_API_KEY"]

def chiama_huggingface_testo(pittore, soggetto):
    """Genera un'analisi stilistica profonda e specifica."""
    api_url = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    
    # Prompt più sofisticato per forzare la specificità dello stile
    prompt_formattato = f"<s>[INST] Sei un critico d'arte esperto. Analizza come l'estetica unica di {pittore} (tecnica, uso del colore, gestione della luce e texture) trasformerebbe il soggetto '{soggetto}'. Rispondi in italiano con un tono colto e descrittivo. [/INST]"
    
    payload = {
        "inputs": prompt_formattato,
        "parameters": {"max_new_tokens": 400, "temperature": 0.8}
    }
    
    try:
        response = requests.post(api_url, headers=headers, json=payload)
        if response.status_code == 200:
            risultato = response.json()
            return risultato[0]['generated_text'].split("[/INST]")[-1].strip()
        else:
            return f"L'opera rifletterebbe la visione distintiva di {pittore} applicata a {soggetto}."
    except:
        return "Analisi stilistica in corso di elaborazione."

def genera_immagine_huggingface(pittore, soggetto):
    """Genera l'immagine forzando i tratti somatici e stilistici del pittore."""
    api_url = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    
    # Prompt migliorato per la specificità dello stile
    # 'In the signature style of' e 'detailed brushwork' aiutano molto
    prompt_artistico = (
        f"A masterpiece painting of {soggetto} in the unmistakable and specific style of {pittore}. "
        f"Signature brushstrokes of {pittore}, authentic color palette, "
        f"masterful lighting and texture typical of {pittore}'s era. "
        f"High quality, oil on canvas texture, 8k resolution, artistic integrity."
    )
    
    payload = {"inputs": prompt_artistico}
    response = requests.post(api_url, headers=headers, json=payload)
    if response.status_code == 200:
        return response.content
    else:
        raise Exception("Il server artistico è occupato. Riprova tra un istante.")

# --- Classe PDF ---
class PDF(FPDF):
    def header(self):
        if self.page_no() == 1:
            self.set_font('Arial', 'B', 22)
            self.cell(0, 15, 'IL PENNELLO DEL TEMPO', 0, 1, 'C')
            self.ln(5)

def crea_pdf_completo(pittore, soggetto, testo_analisi, immagine_bytes):
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 15)
    pdf.cell(0, 10, f"Interpretazione di {soggetto} - Stile: {pittore}", 0, 1, 'L')
    pdf.ln(5)
    pdf.set_font("Arial", size=11)
    testo_pulito = testo_analisi.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 7, txt=testo_pulito)

    if immagine_bytes:
        pdf.add_page(orientation='L')
        with open("temp_print.jpg", "wb") as f:
            f.write(immagine_bytes)
        pdf.image("temp_print.jpg", x=10, y=10, w=277) 
        os.remove("temp_print.jpg")
    
    return pdf.output(dest='S').encode('latin-1')

# --- Layout Streamlit ---
st.set_page_config(page_title="Il Pennello del Tempo", layout="wide")

st.title("🎨 Il Pennello del Tempo")
st.markdown("---")

# Session State
if 'risultati' not in st.session_state:
    st.session_state.risultati = None

# Input
c1, c2 = st.columns(2)
p_in = c1.text_input("Nome del Pittore (es: Van Gogh, Caravaggio, Klimt)")
s_in = c2.text_input("Soggetto (es: Un astronauta, Roma, Un gatto)")

if st.button("Genera Visione Artistica"):
    if p_in and s_in:
        with st.spinner(f"Sto studiando lo stile di {p_in}..."):
            analisi = chiama_huggingface_testo(p_in, s_in)
            try:
                immagine = genera_immagine_huggingface(p_in, s_in)
                st.session_state.risultati = {
                    "analisi": analisi,
                    "immagine": immagine,
                    "pittore": p_in,
                    "soggetto": s_in
                }
            except Exception as e:
                st.error(str(e))
    else:
        st.warning("Inserisci sia il pittore che il soggetto.")

# --- Visualizzazione ---
if st.session_state.risultati:
    res = st.session_state.risultati
    
    st.markdown("### 🖋️ L'Analisi Stilistica")
    st.info(res["analisi"])
    
    st.markdown("### 🖼️ L'Opera")
    st.image(res["immagine"], use_container_width=True, caption=f"{res['soggetto']} reinterpretato da {res['pittore']}")
    
    # Download
    pdf_out = crea_pdf_completo(res["pittore"], res["soggetto"], res["analisi"], res["immagine"])
    st.download_button(
        label="💾 Scarica Dossier Artistico (PDF)",
        data=pdf_out,
        file_name=f"Analisi_{res['pittore']}.pdf",
        mime="application/pdf"
    )
