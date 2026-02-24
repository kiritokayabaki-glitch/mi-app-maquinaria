import streamlit as st
import imaplib
import email
from email.header import decode_header
import time

# --- CONFIGURACIÓN ---
EMAIL_USUARIO = "kiritokayabaki@gmail.com" 
EMAIL_PASSWORD = "wkpn qayc mtqj ucut"

# --- FUNCIONES DE GMAIL ---
def decodificar_texto(texto, encoding):
    try:
        if isinstance(texto, bytes):
            return texto.decode(encoding or "utf-8", errors="replace")
        return str(texto)
    except: return "Texto no legible"

def obtener_cuerpo(mensaje):
    cuerpo = ""
    if mensaje.is_multipart():
        for parte in mensaje.walk():
            if parte.get_content_type() == "text/plain":
                try:
                    cuerpo = parte.get_payload(decode=True).decode("utf-8", errors="replace")
                    break
                except: pass
    else:
        try: cuerpo = mensaje.get_payload(decode=True).decode("utf-8", errors="replace")
        except: pass
    return cuerpo[:500]

def leer_correos():
    try:
        imap = imaplib.IMAP4_SSL("imap.gmail.com")
        imap.login(EMAIL_USUARIO, EMAIL_PASSWORD)
        imap.select("INBOX")
        status, mensajes = imap.search(None, 'ALL')
        ids = mensajes[0].split()
        lista = []
        for i in reversed(ids[-10:]):
            msg_id = i.decode() 
            res, msg = imap.fetch(i, "(RFC822)")
            for respuesta in msg:
                if isinstance(respuesta, tuple):
                    mensaje = email.message_from_bytes(respuesta[1])
                    asunto_raw = decode_header(mensaje["Subject"])[0]
                    asunto = decodificar_texto(asunto_raw[0], asunto_raw[1])
                    contenido = obtener_cuerpo(mensaje)
                    lista.append({"id": msg_id, "Asunto": asunto, "De": mensaje.get("From"), "Cuerpo": contenido})
        imap.logout()
        return lista
    except: return []

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Gestión Maquinaria Pro", layout="wide")

# Inicializar memoria de datos
if "db_comentarios" not in st.session_state:
    st.session_state.db_comentarios = {}
if "lista_correos" not in st.session_state:
    st.session_state.lista_correos = leer_correos()

# --- ESTA ES LA FUNCIÓN "MÁGICA" ANTI-PARPADEO ---
@st.fragment(run_every="15s")
def mostrar_y_actualizar_correos():
    # Esta parte se actualiza sola cada 15 seg SIN refrescar toda la pantalla
    st.session_state.lista_correos = leer_correos()
    
    if st.session_state.lista_correos:
        for item in st.session_state.lista_correos:
            uid = item['id']
            with st.expander(f"📋 ORDEN: {item['Asunto']}", expanded=True):
                col_info, col_registro = st.columns([1, 1])
                
                with col_info:
                    st.write(f"**De:** {item['De']}")
                    st.info(f"**Mensaje:**\n{item['Cuerpo']}")
                
                with col_registro:
                    # Recuperar comentario guardado
                    valor_previo = st.session_state.db_comentarios.get(uid, "")
                    
                    nuevo_comentario = st.text_area(
                        "Comentario del Técnico:", 
                        value=valor_previo, 
                        key=f"input_{uid}"
                    )
                    
                    # Guardar al escribir
                    if nuevo_comentario != valor_previo:
                        st.session_state.db_comentarios[uid] = nuevo_comentario
                    
                    # Estado
                    if st.session_state.db_comentarios.get(uid, "").strip():
                        st.success("🟢 ESTADO: ATENDIDA")
                    else:
                        st.error("🔴 ESTADO: PENDIENTE")
                    
                    c1, c2 = st.columns(2)
                    with c1: st.file_uploader("🖼️ Anteriormente", key=f"ant_{uid}")
                    with c2: st.file_uploader("📸 Actual", key=f"act_{uid}")
                st.divider()

# --- CUERPO PRINCIPAL ---
st.title("🚜 Panel de Control Inteligente")
st.write("Actualización silenciosa activa. Puedes escribir sin interrupciones.")

# Llamamos a la función fragmentada
mostrar_y_actualizar_correos()
