import streamlit as st
import urllib.parse
import random

# Configurazione base
st.set_page_config(page_title="Il Pennello del Tempo", page_icon="🎨")
st.title("🎨 Il Pennello del Tempo")
st.write("Genera un'opera d'arte originale basata sullo stile di un grande maestro.")

# Input semplici e chiari
col1, col2 = st.columns(2)
pittore = col1.text_input("Pittore (es. Van Gogh, Caravaggio, Magritte)")
soggetto = col2.text_input("Soggetto (es. una città futuristica, un gatto)")

if st.button("Genera Visione Artistica"):
    if pittore and soggetto:
        with st.spinner(f"Il maestro {pittore} sta preparando la tela..."):
            # 1. Creiamo un prompt ricco per un'interpretazione originale
            prompt_artistico = (
                f"A unique and original masterpiece oil painting of {soggetto}, "
                f"completely reimagined in the iconic artistic style of {pittore}. "
                f"High quality, museum lighting, detailed textures."
            )
            
            # 2. Codifichiamo per l'URL
            prompt_encoded = urllib.parse.quote(prompt_artistico)
            
            # 3. Generiamo un numero casuale (Seed) per variare ogni singola opera
            seed = random.randint(1, 999999)
            
            # 4. Costruiamo l'URL di Pollinations (stabile e veloce)
            # Usiamo parametri per forzare la rigenerazione ed evitare la cache
            image_url = f"https://image.pollinations.ai/prompt/{prompt_encoded}?width=1024&height=768&nologo=true&seed={seed}"
            
            # 5. Visualizzazione diretta (evita il sovraccarico del server)
            st.image(image_url, caption=f"'{soggetto}' nell'interpretazione di {pittore}", use_container_width=True)
            
            st.success("Opera completata!")
            st.balloons()
    else:
        st.warning("Inserisci entrambi i campi per procedere.")

# Nota a fondo pagina
st.caption("Nota: L'immagine è generata in tempo reale. Puoi salvarla cliccando con il tasto destro sull'immagine.")
