import streamlit as st
import google.generativeai as genai
from fpdf import FPDF
import io # Per gestire l'immagine in memoria
import json
from google.oauth2 import service_account
import vertexai

# Legge i secret dal formato TOML
gcp_creds_dict = st.secrets["gcp"]

# Crea le credenziali
creds = service_account.Credentials.from_service_account_info(gcp_creds_dict)

# Inizializza Vertex AI
vertexai.init(project=gcp_creds_dict["project_id"], credentials=creds)

def genera_immagine_vertex(prompt):
    model = ImageGenerationModel.from_pretrained("imagen-3.0-generate-001")
    images = model.generate_images(
        prompt=prompt,
        number_of_images=1,
        aspect_ratio="16:9",
        safety_filter_level="block_medium_and_above",
        person_generation="allow_adult",
    )
    return images[0] # Ritorna il primo oggetto immagine

# --- Configurazione API ---
# Assicurati che API_KEY sia configurata in .streamlit/secrets.toml
# o nelle Streamlit Cloud secrets
genai.configure(api_key=st.secrets["API_KEY"])

# --- Funzione PDF (come prima) ---
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Analisi Artistica e Opera Generata', 0, 1, 'C')

def crea_pdf_con_immagine(testo_analisi, immagine_bytes=None):
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, txt=testo_analisi.encode('latin-1', 'replace').decode('latin-1'))

    if immagine_bytes:
        pdf.ln(10) # Line break
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, 'Opera Generata:', 0, 1, 'L')
        # Salva l'immagine temporaneamente per FPDF
        with open("temp_image.png", "wb") as f:
            f.write(immagine_bytes)
        pdf.image("temp_image.png", x=10, w=100) # w=100 per ridimensionarla
        # Rimuovi l'immagine temporanea dopo l'uso
        import os
        os.remove("temp_image.png")
    
    return pdf.output(dest='S').encode('latin-1')

# --- Configurazione Pagina Streamlit ---
st.set_page_config(page_title="Il Pennello del Tempo", page_icon="🎨", layout="wide")
st.title("🎨 Il Pennello del Tempo: Analisi & Creazione")

# --- Controlli Input ---
col1, col2 = st.columns(2)
pittore = col1.text_input("Pittore (es. Vincent van Gogh)")
soggetto = col2.text_input("Soggetto (es. un telefono cellulare)")

# --- Bottone Genera ---
if st.button("Genera Interpretazione Artistica e Immagine"):
    if pittore and soggetto:
        # --- Generazione Testuale ---
        st.subheader("### Analisi Testuale")
        text_model = genai.GenerativeModel('gemini-2.5-flash')

        text_prompt = f"""
        Sei un critico d'arte ed esperto di tecniche pittoriche storiche. 
        Analizza il soggetto '{soggetto}' come se fosse stato dipinto da {pittore}.
        
        Struttura la risposta in tre punti:
        1. **Analisi Tecnica**: Descrivi la pennellata, l'uso del colore e la luce tipica dell'autore.
        2. **Composizione**: Spiega come verrebbe impostata la scena.
        3. **Interpretazione concettuale**: Spiega perché questa scelta stilistica valorizza il soggetto.
        
        Mantieni un tono accademico ma ispirato.
        """
        
        with st.spinner('Analizzando lo stile del maestro...'):
            try:
                text_response = text_model.generate_content(text_prompt)
                analisi_testuale = text_response.text
                st.markdown(analisi_testuale)
            except Exception as e:
                st.error(f"Errore durante la generazione dell'analisi testuale: {e}")
                analisi_testuale = "Errore durante la generazione dell'analisi." # Per evitare errori nel PDF

        st.divider() # Separatore visivo
        
        # --- Generazione Immagine ---
        st.subheader("### Opera Generata")
        # Il nome del modello per la generazione di immagini potrebbe essere diverso.
        # Usa un modello che supporti la generazione di immagini.
        # A seconda della tua configurazione e accesso, potrebbe essere 'gemini-1.5-pro-vision', 'gemini-1.0-pro-vision'
        # o un modello dedicato come Imagen 2 se hai accesso diretto.
        
        # Per semplicità e maggiore compatibilità, useremo 'gemini-1.5-pro' anche per l'immagine
        # e gli chiederemo di generare un prompt descrittivo per un modello di immagine esterno.
        # Idealmente, qui useresti un modello specifico per immagini (es. 'imagen-2' se accessibile).
        
        # Generiamo un prompt descrittivo dall'LLM testuale per un ipotetico generatore di immagini
        image_prompt_generator_model = genai.GenerativeModel('gemini-2.5-flash')
        
        image_description_prompt = f"""
        Basandoti sullo stile di {pittore} e sul soggetto '{soggetto}', 
        crea una descrizione dettagliata per un generatore di immagini AI. 
        La descrizione deve includere dettagli su:
        - tipo di immagine (dipinto ad olio, acquerello, scultura, ecc.)
        - colori dominanti e tavolozza
        - composizione e inquadratura
        - illuminazione e atmosfera
        - elementi specifici del pittore (es. pennellate, figure distorte, chiaroscuro)
        - dettagli sul soggetto '{soggetto}' nel contesto di quello stile.
        La descrizione deve essere in inglese e avere una lunghezza massima di 150 parole.
        """
        
        with st.spinner('Il generatore AI sta visualizzando l\'opera...'):
            try:
                image_description_response = image_prompt_generator_model.generate_content(image_description_prompt)
                final_image_prompt = image_description_response.text
                st.info(f"Prompt per l'immagine: {final_image_prompt}") # Utile per debug

                # --- Qui useremmo la capacità di generazione immagini di un modello. ---
                # Dato che la libreria `google-generativeai` al momento non ha un metodo diretto
                # per generare *immagini* da zero (come fanno DALL-E o Midjourney) usando un singolo
                # metodo `generate_content` con `imagen-2` via API pubblica,
                # dobbiamo usare il *tag speciale per il tuo ambiente*.
                
                # In un ambiente che supporta direttamente l'embedding e la generazione
                # di immagini da un LLM multimodale, la chiamata sarebbe qualcosa di simile a:
                # image_response = genai.GenerativeModel('imagen-2').generate_image(prompt=final_image_prompt)
                # image_bytes = image_response.image_data # o simile

                # PER LE TUE ESIGENZE: USA IL TAG SPECIALE
                st.write("L'intelligenza artificiale ha creato la tua immagine:")
                st.write(f"Prompt utilizzato: {final_image_prompt}")
                
                # Questa è la riga che invia la richiesta di generazione immagine
                # Il sistema che gestisce il tuo output catturerà questo tag
                # e userà 'final_image_prompt' come input per il suo generatore di immagini.
                # Assicurati che l'ambiente in cui stai eseguendo questo script
                # sia configurato per intercettare il tag e generare un'immagine da esso.
                
                # Qui, per simulare e mostrare come l'immagine verrebbe visualizzata e passata al PDF:
                # In una vera integrazione, 'generated_image_bytes' sarebbe il risultato della generazione.
                # Per ora, useremo un placeholder visivo che verrà sostituito dal tuo sistema.
                
                # Questo è il TAG che DEVI INSERIRE per far sì che il tuo ambiente generi l'immagine
                # e la passi come byte al PDF.
                # Il testo che segue il tag sarà il prompt per l'immagine.
                st.image(f"data:image/png;base64,{final_image_prompt}") # Questo verrà sostituito dal tuo ambiente.
                # La riga sopra è un placeholder. Se il tuo ambiente supporta il tag 
                # e genera un'immagine, la userà.
                # Per il download PDF, avremmo bisogno dei byte dell'immagine reale.

                # Per il momento, assumiamo che il tuo ambiente possa generare l'immagine e
                # te la restituisca in un modo che puoi catturare e passare al PDF.
                # Visto il formato della richiesta, la vera generazione immagine avviene
                # 'dietro le quinte' del tuo ambiente.
                
                # Quindi, per integrare con il PDF, avremmo bisogno che il tuo sistema mi fornisca
                # i byte dell'immagine generata dopo il tag.
                # Per la demo, il PDF includerà solo l'analisi testuale.
                # Se il tuo sistema può fornire l'immagine come bytes dopo la generazione,
                # possiamo includerla nel PDF.
                
                # Per il momento, il tasto PDF conterrà solo l'analisi testuale.
                # Se il tuo ambiente ti restituisce i byte dell'immagine,
                # DEVI CATTURARE QUELLI E PASSARLI ALLA FUNZIONE 'crea_pdf_con_immagine'
                # esempio:
                # generated_image_bytes = cattura_immagine_generata_dal_tuo_ambiente()
                # pdf_data = crea_pdf_con_immagine(analisi_testuale, generated_image_bytes)

        with st.spinner('Il maestro sta dipingendo...'):
            immagine = genera_immagine_vertex(final_image_prompt)
            # Visualizzazione
            st.image(immagine.image_bytes, caption=f"Reinterpretazione di {pittore}")
            
            # Download PDF con immagine inclusa
            pdf_data = crea_pdf_con_immagine(analisi_testuale, immagine.image_bytes)
            st.download_button("💾 Salva PDF Completo", data=crea_pdf_con_immagine(analisi_testuale), # Ora senza immagine per il momento
                    file_name="interpretazione.pdf",
                    mime="application/pdf"
                )

        except Exception as e:
            st.error(f"Errore durante la generazione dell'immagine: {e}")
    else:
        st.warning("Per favore, compila entrambi i campi.")
