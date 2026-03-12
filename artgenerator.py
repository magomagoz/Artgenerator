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
            # Sostituisci la parte della response in genera_immagine_huggingface con:
            response = requests.post(api_url, headers=headers, json={"inputs": prompt}, timeout=30)
            if response.status_code == 200:
                # Controlla se inizia con i byte tipici di un'immagine (es. JPEG o PNG)
                if response.content.startswith(b'\xff\xd8') or response.content.startswith(b'\x89PNG'):
                    return response.content
                else:
                    # Se non è un'immagine, probabilmente è un messaggio di errore (es: "Model is loading")
                    return None 

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
        
        # DEFINIAMO L'AREA SICURA (A4 Landscape è 297x210)
        # Sottraiamo i margini (10mm per lato)
        larghezza_max = 277 
        altezza_max = 180  # Ridotto per evitare che tocchi il fondo o il footer
        
        # Inseriamo l'immagine:
        # Passando sia 'w' che 'h', FPDF di solito deforma. 
        # Per evitare deformazioni, ne passiamo solo uno, ma dobbiamo capire quale.
        # Strategia: la inseriamo con w=277, ma se l'altezza risultante è > 180, 
        # allora la inseriamo forzando l'altezza h=180.
        
        try:
            # Proviamo a inserirla scalata sulla larghezza
            pdf.image("temp_print.jpg", x=10, y=15, w=larghezza_max) 
            
            # Se dopo l'inserimento vediamo che l'altezza occupata è troppa, 
            # FPDF non permette il "undo", quindi usiamo un trucco: 
            # Specifichiamo 'h' invece di 'w' se l'immagine è troppo alta.
            # Per semplicità, forziamo l'altezza massima di sicurezza:
            # pdf.image("temp_print.jpg", x=10, y=15, h=altezza_max)
            
        except Exception as e:
            st.error(f"Errore PDF: {e}")
        finally:
            if os.path.exists("temp_print.jpg"):
                os.remove("temp_print.jpg")
    
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
    if r["t"]:
        st.info(r["t"])
    
    # Controllo di sicurezza prima di mostrare l'immagine
    if r["i"] is not None:
        st.image(r["i"], use_container_width=True)
        pdf_file = crea_pdf(r["p"], r["s"], r["t"], r["i"])
        st.download_button("💾 Scarica PDF", data=pdf_file, file_name=f"{r['p']}.pdf")
    else:
        st.error("L'immagine non è stata generata correttamente. Il server è molto carico.")
