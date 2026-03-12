import streamlit as st
import requests
import time

# --- LOGICA TESTUALE (Indipendente) ---
def genera_analisi_testuale(pittore, soggetto):
    prompt = f"Scrivi un'analisi critica su '{soggetto}' nello stile di {pittore}."
    try:
        # Esempio usando Gemini o un altro modello
        return "Questa è un'analisi profonda dello stile..." 
    except:
        return "Errore nel caricamento dell'analisi."

# --- LOGICA IMMAGINE (Indipendente) ---
def genera_immagine_flux(pittore, soggetto):
    api_url = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell"
    headers = {"Authorization": f"Bearer {st.secrets['HF_API_KEY']}"}
    prompt = f"Oil painting of {soggetto} in the style of {pittore}."
    
    for _ in range(3):
        response = requests.post(api_url, headers=headers, json={"inputs": prompt})
        if response.status_code == 200:
            return response.content
        time.sleep(5)
    return None

# --- UI (Layout a due colonne) ---
st.title("🎨 Il Pennello del Tempo")
p_in = st.text_input("Artista")
s_in = st.text_input("Soggetto")

col1, col2 = st.columns(2)

# PULSANTE 1: ANALISI
if col1.button("Genera Analisi Testuale"):
    with st.spinner("Il critico sta scrivendo..."):
        st.session_state.analisi = genera_analisi_testuale(p_in, s_in)

# PULSANTE 2: IMMAGINE
if col2.button("Genera Visione Visiva"):
    with st.spinner("Il pittore sta dipingendo..."):
        st.session_state.immagine = genera_immagine_flux(p_in, s_in)

# --- VISUALIZZAZIONE ---
if 'analisi' in st.session_state:
    st.info(st.session_state.analisi)

if 'immagine' in st.session_state:
    if st.session_state.immagine:
        st.image(st.session_state.immagine)
    else:
        st.error("L'immagine non è stata generata. Riprova.")

    
    # Download PDF
    pdf = FPDF(unit='mm', format=(400, 280))
    pdf.add_page()
    pdf.set_font("Arial", size=14)
    pdf.multi_cell(0, 10, txt=r["t"].encode('latin-1', 'replace').decode('latin-1'))
    
    # Salva e scarica
    with open("tmp.jpg", "wb") as f: f.write(r["i"])
    pdf.add_page()
    pdf.image("tmp.jpg", x=20, y=20, w=360)
    st.download_button("💾 Scarica Dossier PDF", data=pdf.output(dest='S').encode('latin-1'), file_name="opera.pdf")
