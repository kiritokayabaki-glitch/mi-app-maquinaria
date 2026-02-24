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
        for i in reversed(ids[-5:]):
            res, msg = imap.fetch(i, "(RFC822)")
            for respuesta in msg:
                if isinstance(respuesta, tuple):
                    mensaje = email.message_from_bytes(respuesta[1])
                    asunto, cod = decode_header(mensaje["Subject"])[0]
                    if isinstance(asunto, bytes): asunto = asunto.decode(cod or "utf-8")
                    lista.append({"Asunto": asunto, "De": mensaje.get("From")})
        imap.logout()
        return lista
    except Exception as e: return f"Error: {e}"

st.title("🚜 Mis Eventos de Maquinaria")
if st.button("📥 Sincronizar Correos"):
    datos = leer_correos()
    if isinstance(datos, list):
        for item in datos:
            st.info(f"📩 {item['Asunto']} \n\n De: {item['De']}")
    else: st.error(datos)
