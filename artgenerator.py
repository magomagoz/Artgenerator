import streamlit as st
import urllib.parse
import requests
import random

# Configurazione base
st.set_page_config(page_title="Il Pennello del Tempo", page_icon="🎨")
st.title("🎨 Il Pennello del Tempo")

# Input utente
col1, col2 = st.columns(2)
pittore = col1.text_input("Pittore (es. Van Gogh, Caravaggio)")
soggetto = col2.text_input("Soggetto (es. una città futuristica)")

if st.button("Genera Visione Artistica"):
    if pittore and soggetto:
        with st.spinner(f"Il maestro {pittore} sta dipingendo..."):
            # 1. Creiamo il prompt
            prompt_artistico = f"A unique oil painting of {soggetto} in the style of {pittore}, masterpiece, high quality."
            prompt_encoded = urllib.parse.quote(prompt_artistico)
            seed = random.randint(1, 999999)
            
            # 2. URL del servizio
            image_url = f"https://image.pollinations.ai/prompt/{prompt_encoded}?width=1024&height=768&nologo=true&seed={seed}"
            
            try:
                # 3. FORZIAMO lo scaricamento dell'immagine dal server
                # Questo evita il quadratino col punto interrogativo
                response = requests.get(image_url, timeout=30)
                
                if response.status_code == 200:
                    # 4. Visualizziamo i dati BINARI dell'immagine (metodo più sicuro)
                    st.image(response.content, caption=f"{soggetto} in stile {pittore}", use_container_width=True)
                    st.success("Opera completata!")

                st.download_button(
                label="💾 Scarica questa opera",
                data=response.content,
                file_name=f"{soggetto}_{pittore}.jpg",
                mime="image/jpeg"
            )
            else:
                st.error("Il servizio di pittura è momentaneamente occupato. Riprova tra pochi secondi.")
        except Exception as e:
            st.error(f"Errore di connessione: {e}")
    #else:
        #st.warning("Inserisci entrambi i campi.")
