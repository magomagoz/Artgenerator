import streamlit as st
import urllib.parse
import requests
import random

# Configurazione base
st.set_page_config(page_title="Il Pennello del Tempo", page_icon="🎨", layout=wide)
st.image("banner3.png")
#st.title("🎨 Il Pennello del Tempo")

# Input utente
col1, col2 = st.columns(2)
pittore = col1.text_input("🎨 Pittore (es. Van Gogh, Caravaggio)")
soggetto = col2.text_input("Soggetto (es. una città futuristica)")

if st.button("Genera Visione Artistica"):
    if pittore and soggetto:
        with st.spinner(f"Il maestro {pittore} sta dipingendo..."):
            # 1. Creiamo il prompt
            prompt_artistico = f"Sono il pittore {pittore}, esperto del mio stile creativo e del mio tempo. Utilizzerò tutte le mie peculiarità per creare una immagine originale che rappresenti il {soggetto} e che sia immediatamente accostabile al mio specifico stile"
            prompt_encoded = urllib.parse.quote(prompt_artistico)
            seed = random.randint(1, 999999)
            
            # 2. URL del servizio
            image_url = f"https://image.pollinations.ai/prompt/{prompt_encoded}?width=1024&height=768&nologo=true&seed={seed}"
            
            try:
                # 3. Scarichiamo l'immagine dal server per stabilità
                response = requests.get(image_url, timeout=30)
                
                if response.status_code == 200:
                    # 4. Visualizziamo l'immagine
                    st.image(response.content, caption=f"{soggetto} in stile {pittore}", use_container_width=True)
                    st.success("Opera completata!")
                    
                    # 5. Tasto per scaricare l'immagine
                    st.download_button(
                        label="💾 Scarica questa opera",
                        data=response.content,
                        file_name=f"{soggetto}_{pittore}.jpg",
                        mime="image/jpeg"
                    )
                else:
                    st.error("Il servizio è momentaneamente occupato. Riprova tra pochi secondi.")
            
            except Exception as e:
                st.error(f"Errore di connessione: {e}")
    else:
        st.warning("Per favore, inserisci sia l'artista che il soggetto.")
