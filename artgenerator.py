import streamlit as st
import urllib.parse
import requests
import random

# Configurazione base
st.set_page_config(page_title="Il Pennello del Tempo", page_icon="🎨", layout="wide")
st.image("banner3.png")
#st.title("🎨 Il Pennello del Tempo")

# Inizializziamo lo stato della sessione se non esiste
if 'immagine_fatta' not in st.session_state:
    st.session_state.immagine_fatta = None
if 'pittore_fatto' not in st.session_state:
    st.session_state.pittore_fatto = ""
if 'soggetto_fatto' not in st.session_state:
    st.session_state.soggetto_fatto = ""

# Input utente
col1, col2 = st.columns(2)
pittore = col1.text_input("🎨 Pittore (es. Van Gogh, Caravaggio)")
soggetto = col2.text_input("Soggetto (es. una città futuristica)")

if st.button("Genera Visione Artistica"):
    if pittore and soggetto:
        with st.spinner(f"Il maestro {pittore} sta dipingendo..."):
            # 1. Creiamo il prompt
            prompt_artistico = (
                f"I am the painter {pittore}, a master of my unique creative style and my historical era. "
                f"I will now employ all my signature techniques and artistic vision to create an "
                f"original masterpiece representing '{soggetto}'. This artwork must be instantly "
                f"recognizable as my own work, capturing my specific brushwork, use of light, and emotional depth "
                f"oil on canvas, museum quality, 8k resolution, highly detailed textures."
            )
            prompt_encoded = urllib.parse.quote(prompt_artistico)
            seed = random.randint(1, 999999)
            
            # 2. URL del servizio
            image_url = f"https://image.pollinations.ai/prompt/{prompt_encoded}?width=1024&height=768&nologo=true&seed={seed}"
            
            try:
                response = requests.get(image_url, timeout=30)
                if response.status_code == 200:
                    # SALVIAMO NELLO STATO DELLA SESSIONE
                    st.session_state.immagine_fatta = response.content
                    st.session_state.pittore_fatto = pittore
                    st.session_state.soggetto_fatto = soggetto
                else:
                    st.error("Servizio momentaneamente occupato.")
            except Exception as e:
                st.error(f"Errore: {e}")
    else:
        st.warning("Inserisci entrambi i campi.")

# MOSTRA L'IMMAGINE PERSISTENTE (se esiste nello stato della sessione)
if st.session_state.immagine_fatta is not None:
    st.image(st.session_state.immagine_fatta, 
             caption=f"{st.session_state.soggetto_fatto} in stile {st.session_state.pittore_fatto}", 
             use_container_width=True)
    
    st.success("Opera completata!")
    
    # Il pulsante di download ora non farà sparire nulla
    st.download_button(
        label="💾 Scarica questa opera",
        data=st.session_state.immagine_fatta,
        file_name=f"{st.session_state.soggetto_fatto}_{st.session_state.pittore_fatto}.jpg",
        mime="image/jpeg"
    )
