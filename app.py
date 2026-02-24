import streamlit as st
import imaplib
import email
from email.header import decode_header
import pandas as pd

# --- CONFIGURACIÓN DE SEGURIDAD ---
# REEMPLAZA ESTO CON TUS DATOS REALES
EMAIL_USUARIO = "kiritokayabaki@gmail.com" 
EMAIL_PASSWORD = "wkpn qayc mtqj ucut" # Pega aquí las 16 letras sin espacios

def leer_correos():
    try:
        imap = imaplib.IMAP4_SSL("imap.gmail.com")
        imap.login(EMAIL_USUARIO, EMAIL_PASSWORD)
        imap.select("INBOX")

        # Buscamos correos (puedes filtrar por remitente o palabra clave)
        status, mensajes = imap.search(None, 'ALL')
        ids = mensajes[0].split()
        
        lista_final = []
        # Tomamos los últimos 10 correos para revisar
        for i in reversed(ids[-10:]):
            res, msg = imap.fetch(i, "(RFC822)")
            for respuesta in msg:
                if isinstance(respuesta, tuple):
                    mensaje = email.message_from_bytes(respuesta[1])
                    asunto, codificacion = decode_header(mensaje["Subject"])[0]
                    if isinstance(asunto, bytes):
                        asunto = asunto.decode(codificacion or "utf-8")
                    
                    remitente = mensaje.get("From")
                    fecha = mensaje.get("Date")
                    
                    lista_final.append({
                        "Fecha": fecha,
                        "De": remitente,
                        "Asunto": asunto
                    })
        imap.logout()
        return lista_final
    except Exception as e:
        return f"Error: {e}"

# --- INTERFAZ TIPO APPSHEET ---
st.set_page_config(page_title="Eventos de Servicio", layout="centered")

st.markdown("<h2 style='text-align: center; color: #f39c12;'>📅 Panel de Eventos</h2>", unsafe_allow_html=True)

if st.button("📥 Sincronizar con Gmail"):
    with st.spinner("Buscando correos nuevos..."):
        datos = leer_correos()
        
        if isinstance(datos, list):
            for item in datos:
                with st.container():
                    st.markdown(f"""
                    <div style="border: 1px solid #ddd; border-radius: 10px; padding: 15px; margin-bottom: 10px; background-color: white;">
                        <h4 style="margin:0; color: #333;">{item['Asunto']}</h4>
                        <p style="margin:0; font-size: 0.8em; color: #666;">{item['De']} | {item['Fecha']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Botones de acción como en AppSheet
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("📝 Comentar", key=f"coment_{item['Asunto']}"):
                            st.info("Función de guardado en preparación...")
                    with col2:
                        st.file_uploader("📷 Subir Foto", key=f"foto_{item['Asunto']}")
        else:
            st.error(datos)