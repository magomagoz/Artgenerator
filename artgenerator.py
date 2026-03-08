import streamlit as st
import google.generativeai as genai
from fpdf import FPDF

# Configurazione API
genai.configure(api_key=st.secrets["API_KEY"])

# Funzione per trovare il modello giusto
def get_available_model():
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            return m.name
    return None

model_name = get_available_model()
model = genai.GenerativeModel(model_name)

st.sidebar.write(f"Modello in uso: {model_name}") # Ti aiuterà a capire cosa sta succedendo

#model = genai.GenerativeModel('gemini-1.5-pro') # Versione più moderna e veloce

st.set_page_config(page_title="Interpretazioni d'Arte", page_icon="🎨", layout = "wide")
st.image("banner.png")
#st.title("🎨 Il Pennello del Tempo")

def crea_pdf(testo):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    # Gestione caratteri italiani
    testo_encoded = testo.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 10, txt=testo_encoded)
    return pdf.output(dest='S').encode('latin-1')

col1, col2 = st.columns(2)
pittore = col1.text_input("Pittore (es. Van Gogh)")
soggetto = col2.text_input("Soggetto (es. uno smartphone)")

if st.button("Genera Interpretazione"):
    if pittore and soggetto:
        prompt = f"""
        Agisci come un esperto storico dell'arte. Analizza il soggetto '{soggetto}' 
        reinterpretandolo attraverso la tecnica pittorica di {pittore}.
        
        Struttura la risposta in:
        1. **Analisi Tecnica**: Pennellata, luce, tavolozza.
        2. **Composizione**: Impostazione spaziale.
        3. **Interpretazione concettuale**: Senso filosofico dell'opera.
        """
        
        with st.spinner('Il maestro sta dipingendo...'):
            try:
                response = model.generate_content(prompt)
                analisi = response.text
                
                # Visualizzazione output
                st.markdown("### Interpretazione Artistica")
                st.markdown(analisi)
                
                # Tasto download (appare solo se c'è l'analisi)
                st.download_button(
                    label="💾 Salva Analisi in PDF",
                    data=crea_pdf(analisi),
                    file_name="interpretazione.pdf",
                    mime="application/pdf"
                )
            except Exception as e:
                st.error(f"Errore durante la generazione: {e}")
    else:
        st.warning("Per favore, compila entrambi i campi.")
