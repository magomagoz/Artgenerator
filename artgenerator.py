import streamlit as st
from fpdf import FPDF
import io 
import os
import requests

# --- Configurazione API ---
HF_API_KEY = st.secrets["HF_API_KEY"]

def chiama_huggingface_testo(pittore, soggetto):
    """Genera l'analisi testuale usando un modello affidabile di Hugging Face."""
    # Usiamo un endpoint più generico e stabile per evitare l'errore 404
    api_url = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    
    prompt_formattato = f"<s>[INST] Sei un critico d'arte. Descrivi in italiano come l'artista {pittore} dipingerebbe '{soggetto}'. Parla di stile e colori. [/INST]"
    
    payload = {
        "inputs": prompt_formattato,
        "parameters": {"max_new_tokens": 300, "temperature": 0.7}
    }
    
    try:
        response = requests.post(api_url, headers=headers, json=payload)
        if response.status_code == 200:
            risultato = response.json()
            # Pulizia della risposta per estrarre solo il testo generato
            testo = risultato[0]['generated_text'].split("[/INST]")[-1].strip()
            return testo
        else:
            return f"Analisi stile: {pittore} interpreterebbe {soggetto} con la sua tipica maestria, focalizzandosi su contrasti e forme espressive."
    except:
        return "Analisi generica: Un'opera che fonde la visione del maestro con il soggetto scelto."

def genera_immagine_huggingface(prompt):
    """Genera l'immagine usando Stable Diffusion XL."""
    api_url = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    payload = {"inputs": prompt}
    response = requests.post(api_url, headers=headers, json=payload)
    if response.status_code == 200:
        return response.content
    else:
        raise Exception("Servizio immagini momentaneamente occupato.")

# --- Classe PDF (Corretta per JPG) ---
class PDF(FPDF):
    def header(self):
        if self.page_no() == 1:
            self.set_font('Arial', 'B', 20)
            self.cell(0, 15, 'IL PENNELLO DEL TEMPO', 0, 1, 'C')
            self.ln(5)

def crea_pdf_completo(pittore, soggetto, testo_analisi, immagine_bytes):
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, f"Soggetto: {soggetto} | Stile: {pittore}", 0, 1, 'L')
    pdf.ln(5)
    pdf.set_font("Arial", size=11)
    # Codifica sicura per evitare crash con caratteri speciali
    testo_pulito = testo_analisi.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 7, txt=testo_pulito)

    if immagine_bytes:
        pdf.add_page(orientation='L')
        # Salviamo come .jpg per compatibilità con l'output di HF
        with open("temp_print.jpg", "wb") as f:
            f.write(immagine_bytes)
        pdf.image("temp_print.jpg", x=10, y=10, w=277) 
        os.remove("temp_print.jpg")
    
    return pdf.output(dest='S').encode('latin-1')

# --- Layout Streamlit ---
st.set_page_config(page_title="Il Pennello del Tempo", layout="wide")

st.title("🎨 Il Pennello del Tempo")

# Inizializzazione Sessione
if 'risultati' not in st.session_state:
    st.session_state.risultati = None

# Input in colonna
c1, c2 = st.columns(2)
p_in = c1.text_input("Artista")
s_in = c2.text_input("Soggetto")

if st.button("Genera Opera Completa"):
    if p_in and s_in:
        with st.spinner('Il sistema sta creando...'):
            analisi = chiama_huggingface_testo(p_in, s_in)
            try:
                img_prompt = f"Professional oil painting of {s_in} by {p_in}, masterpiece, detailed."
                immagine = genera_immagine_huggingface(img_prompt)
                
                st.session_state.risultati = {
                    "analisi": analisi,
                    "immagine": immagine,
                    "pittore": p_in,
                    "soggetto": s_in
                }
            except Exception as e:
                st.error(f"Errore: {e}")
    else:
        st.warning("Compila i campi!")

# --- Visualizzazione Verticale ---
if st.session_state.risultati:
    res = st.session_state.risultati
    
    st.divider()
    st.subheader("🖋️ Analisi del Critico")
    st.info(res["analisi"])
    
    st.divider()
    st.subheader("🖼️ L'Opera d'Arte")
    st.image(res["immagine"], use_container_width=True)
    
    # Download PDF
    pdf_out = crea_pdf_completo(res["pittore"], res["soggetto"], res["analisi"], res["immagine"])
    st.download_button("💾 Scarica PDF", data=pdf_out, file_name="opera_artistica.pdf", mime="application/pdf")
