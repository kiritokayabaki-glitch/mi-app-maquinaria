import streamlit as st
import imaplib
import email
from email.header import decode_header

# --- CONFIGURACIÓN DE SEGURIDAD ---
EMAIL_USUARIO = "kiritokayabaki@gmail.com" 
EMAIL_PASSWORD = "wkpn qayc mtqj ucut" 

def leer_correos():
    try:
        imap = imaplib.IMAP4_SSL("imap.gmail.com")
        imap.login(EMAIL_USUARIO, EMAIL_PASSWORD)
        imap.select("INBOX")
        status, mensajes = imap.search(None, 'ALL')
        ids = mensajes[0].split()
        lista = []
        
        # Revisamos los últimos 5 correos
        for i in reversed(ids[-5:]):
            res, msg = imap.fetch(i, "(RFC822)")
            for respuesta in msg:
                if isinstance(respuesta, tuple):
                    mensaje = email.message_from_bytes(respuesta[1])
                    asunto_raw = decode_header(mensaje["Subject"])[0]
                    asunto = asunto_raw[0]
                    codificacion = asunto_raw[1]
                    
                    # --- AQUÍ ESTÁ EL ARREGLO PARA EL ERROR ---
                    try:
                        if isinstance(asunto, bytes):
                            # Si no reconoce la codificación, usamos 'latin-1' o 'utf-8' por defecto
                            asunto = asunto.decode(codificacion or "utf-8", errors="replace")
                    except:
                        asunto = str(asunto) # Si falla, que lo ponga como texto simple
                    
                    lista.append({"Asunto": asunto, "De": mensaje.get("From")})
        
        imap.logout()
        return lista
    except Exception as e:
        return f"Error: {e}"

# --- INTERFAZ ---
st.set_page_config(page_title="Eventos Maquinaria", page_icon="🚜")
st.title("🚜 Mis Eventos de Maquinaria")

if st.button("📥 Sincronizar Correos"):
    with st.spinner("Conectando con Gmail..."):
        datos = leer_correos()
        if isinstance(datos, list):
            if not datos:
                st.warning("No se encontraron correos.")
            for item in datos:
                with st.expander(f"📩 {item['Asunto']}"):
                    st.write(f"**De:** {item['De']}")
                    st.text_area("Comentario", key=f"txt_{item['Asunto']}")
                    st.file_uploader("Subir foto", key=f"img_{item['Asunto']}")
                    if st.button("Guardar reporte", key=f"btn_{item['Asunto']}"):
                        st.success("Reporte guardado localmente")
        else:
            st.error(datos)
