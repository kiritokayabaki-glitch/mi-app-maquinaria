import streamlit as st
import imaplib
import email
from email.header import decode_header

# --- CONFIGURACIÓN ---
EMAIL_USUARIO = "kiritokayabaki@gmail.com" 
EMAIL_PASSWORD = "wkpn qayc mtqj ucut" # Tu código de 16 letras

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
        imap.select("INBOX") # <-- Cambia a "[Gmail]/Todos" si no ves nada
        
        # Buscamos TODOS los correos
        status, mensajes = imap.search(None, 'ALL')
        ids = mensajes[0].split()
        
        if not ids:
            return "No se encontraron correos en la bandeja de entrada."
            
        lista = []
        # Traemos los últimos 10 para asegurar que algo aparezca
        for i in reversed(ids[-10:]):
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
    except Exception as e:
        return f"Error de conexión: {e}"

# --- INTERFAZ ---
st.set_page_config(page_title="Gestión de Maquinaria", layout="wide")
st.title("🚜 Control de Notificaciones")

# Inicializamos el estado si no existe
if "lista_correos" not in st.session_state:
    st.session_state.lista_correos = []

if st.button("🔄 Sincronizar con Gmail"):
    with st.spinner("Conectando con Gmail..."):
        resultado = leer_correos()
        if isinstance(resultado, list):
            st.session_state.lista_correos = resultado
            if not resultado:
                st.warning("La conexión fue exitosa, pero la carpeta está vacía.")
        else:
            st.error(resultado)

# Mostrar los correos guardados en el estado
if st.session_state.lista_correos:
    for idx, item in enumerate(st.session_state.lista_correos):
        with st.expander(f"📋 {item['Asunto']}", expanded=(idx == 0)):
            col1, col2 = st.columns([2, 1])
            with col1:
                st.write(f"**De:** {item['De']}")
                st.info(f"**Mensaje:**\n{item['Cuerpo']}")
            with col2:
                comentario = st.text_area("Comentario de atención:", key=f"c_{idx}")
                if comentario.strip():
                    st.success("🟢 ATENDIDA")
                    st.checkbox("Notificación atendida", value=True, key=f"ch_{idx}")
                else:
                    st.error("🔴 PENDIENTE")
            st.divider()
