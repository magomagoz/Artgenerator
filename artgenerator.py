import streamlit as st
import urllib.parse

# Configurazione Pagina
st.set_page_config(page_title="Il Pennello del Tempo", page_icon="🎨", layout="centered")

st.title("🎨 Il Pennello del Tempo")
st.subheader("Genera una visione artistica originale")

# Input utente
col1, col2 = st.columns(2)
pittore = col1.text_input("Pittore (es. Monet, Caravaggio, Dalí)")
soggetto = col2.text_input("Soggetto (es. Pechino, un gatto, il mare)")

# Logica di generazione
if st.button("Genera Visione Artistica"):
    if pittore and soggetto:
        with st.spinner(f'Il maestro {pittore} sta dipingendo {soggetto}...'):
            # Creiamo un prompt descrittivo e originale
            prompt_artistico = f"A masterpiece oil painting of {soggetto} in the unique artistic style of {pittore}. Detailed brushwork, authentic colors, museum quality, 8k resolution."
            
            # Codifichiamo il testo per l'URL (trasforma spazi in %20)
            prompt_encoded = urllib.parse.quote(prompt_artistico)
            
            # Costruiamo l'URL di Pollinations (Molto più stabile delle API tradizionali)
            # Aggiungiamo un parametro 'seed' casuale per avere interpretazioni sempre originali
            import random
            seed = random.randint(0, 99999)
            image_url = f"https://image.pollinations.ai/prompt/{prompt_encoded}?width=1024&height=768&nologo=true&seed={seed}"
            
            # Mostriamo l'immagine
            # Passando direttamente l'URL, evitiamo l'errore di "sovraccarico del server"
            st.image(image_url, caption=f"{soggetto} interpretato da {pittore}", use_container_width=True)
            
            # Messaggio di successo
            st.success("Interpretazione completata!")
            
            # Nota tecnica: Per il download del PDF dell'immagine, 
            # servirebbe scaricare i byte, il che potrebbe ridare l'errore di timeout.
            # Per ora, puoi salvare l'immagine cliccando col tasto destro sopra di essa.
            
    else:
        st.warning("Inserisci sia il nome del pittore che il soggetto per iniziare.")

st.info("Consiglio: Sii specifico! Invece di 'Van Gogh', prova 'Van Gogh periodo parigino' per risultati più originali.")
