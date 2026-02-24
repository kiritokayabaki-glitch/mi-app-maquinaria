import streamlit as st
import imaplib
import email
from email.header import decode_header

# --- CONFIGURACIÓN ---
EMAIL_USUARIO = "kiritokayabaki@gmail.com" 
EMAIL_PASSWORD = "wkpn qayc mtqj ucut"

def decodificar_texto(texto, encoding):
    """Función de seguridad para limpiar textos con errores de codificación"""
    try:
        if isinstance(texto, bytes):
            # Si el encoding es desconocido, forzamos utf-8 o latin-1 ignorando errores
            return texto.decode(encoding or "utf-8", errors="replace")
        return str(texto)
    except:
        return "Texto no legible"

def obtener_cuerpo(mensaje):
    cuerpo = ""
    if mensaje.is_multipart():
        for parte in mensaje.walk():
            tipo = parte.get_content_type()
            if tipo == "text/plain":
                try:
                    payload = parte.get_payload(decode=True)
                    cuerpo = payload.decode("utf-8", errors="replace")
                    break
                except: pass
    else:
        try:
            payload = mensaje.get_payload(decode=True)
            cuerpo = payload.decode("utf-8", errors="replace")
        except: pass
    return cuerpo[:500] + "..." if len(cuerpo) > 500 else cuerpo

def leer_correos():
    try:
        imap = imaplib.IMAP4_SSL("imap.gmail.com")
        imap.login(EMAIL_USUARIO, EMAIL_PASSWORD)
        imap.select("INBOX")
        
        status, mensajes = imap.search(None, 'ALL')
        ids = mensajes[0].split()
        
        if not ids:
            return "Bandeja vacía."
            
        lista = []
        for i in reversed(ids[-8:]): # Traemos los últimos 8
            res, msg = imap.fetch(i, "(RFC822)")
            for respuesta in msg:
                if isinstance(respuesta, tuple):
                    mensaje = email.message_from_bytes(respuesta[1])
                    
                    # --- ARREGLO PARA EL ERROR UNKNOWN-8BIT ---
                    asunto_raw = decode_header(mensaje["Subject"])[0]
                    asunto = decodificar_texto(asunto_raw[0], asunto_raw[1])
                    
                    contenido = obtener_cuerpo(mensaje)
                    lista.append({"Asunto": asunto, "De": mensaje.get("From"), "Cuerpo": contenido})
        
        imap.logout()
        return lista
    except Exception as e:
        return f"Error de conexión: {e}"

# --- INTERFAZ ---
st.set_page_config(page_title="Gestión de Maquinaria", layout="wide")
st.title("🚜 Control de Notificaciones")

if "lista_correos" not in st.session_state:
    st.session_state.lista_correos = []

if st.button("🔄 Sincronizar con Gmail"):
    with st.spinner("Limpiando y cargando correos..."):
        st.session_state.lista_correos = leer_correos()

if isinstance(st.session_state.lista_correos, list):
    for idx, item in enumerate(st.session_state.lista_correos):
        with st.expander(f"📋 {item['Asunto']}", expanded=False):
            col1, col2 = st.columns([2, 1])
            with col1:
                st.write(f"**De:** {item['De']}")
                st.info(f"**Mensaje:**\n{item['Cuerpo']}")
            with col2:
                comentario = st.text_area("Comentario de atención:", key=f"c_{idx}")
                if comentario.strip():
                    st.success("🟢 ATENDIDA")
                    st.checkbox("Confirmar", value=True, key=f"ch_{idx}")
                else:
                    st.error("🔴 PENDIENTE")
            st.divider()
