import streamlit as st
import imaplib
import email
from email.header import decode_header

# --- CONFIGURACIÓN ---
EMAIL_USUARIO = "kiritokayabaki@gmail.com" 
EMAIL_PASSWORD = "wkpn qayc mtqj ucut" 

def obtener_cuerpo(mensaje):
    cuerpo = ""
    if mensaje.is_multipart():
        for parte in mensaje.walk():
            tipo = parte.get_content_type()
            if tipo == "text/plain":
                try:
                    cuerpo = parte.get_payload(decode=True).decode("utf-8", errors="replace")
                    break
                except: pass
    else:
        try:
            cuerpo = mensaje.get_payload(decode=True).decode("utf-8", errors="replace")
        except: pass
    return cuerpo[:500] + "..." if len(cuerpo) > 500 else cuerpo

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
                    asunto_raw = decode_header(mensaje["Subject"])[0]
                    asunto = asunto_raw[0]
                    if isinstance(asunto, bytes):
                        asunto = asunto.decode(asunto_raw[1] or "utf-8", errors="replace")
                    contenido = obtener_cuerpo(mensaje)
                    lista.append({"Asunto": asunto, "De": mensaje.get("From"), "Cuerpo": contenido})
        imap.logout()
        return lista
    except Exception as e: return f"Error: {e}"

# --- INTERFAZ ---
st.set_page_config(page_title="Gestión de Maquinaria", layout="wide")
st.title("🚜 Control de Notificaciones de Servicio")

# Usamos 'session_state' para que los correos no desaparezcan al escribir
if "correos" not in st.session_state:
    st.session_state.correos = []

if st.button("🔄 Sincronizar con Gmail"):
    st.session_state.correos = leer_correos()

if isinstance(st.session_state.correos, list):
    for idx, item in enumerate(st.session_state.correos):
        with st.expander(f"📋 {item['Asunto']}", expanded=True):
            col_info, col_accion = st.columns([2, 1])
            
            with col_info:
                st.write(f"**Remitente:** {item['De']}")
                st.info(f"**Detalle:** {item['Cuerpo']}")
            
            with col_accion:
                # --- LÓGICA DE ESTADO ---
                comentario = st.text_area("Escribir comentario de atención:", key=f"coment_{idx}")
                
                if comentario.strip() == "":
                    st.error("🔴 Estado: PENDIENTE")
                    atendida = False
                else:
                    st.success("🟢 Estado: ATENDIDA")
                    atendida = st.checkbox("Confirmar notificación atendida", value=True, key=f"check_{idx}")
                
                st.file_uploader("Adjuntar evidencia (foto)", key=f"foto_{idx}")
                
                if st.button("💾 Guardar Reporte", key=f"btn_{idx}"):
                    if comentario:
                        st.balloons()
                        st.toast(f"Reporte de '{item['Asunto']}' guardado con éxito.")
                    else:
                        st.warning("Debes agregar un comentario para finalizar.")
            st.divider()
