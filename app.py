import streamlit as st
import imaplib
import email
from email.header import decode_header
import time

# --- CONFIGURACIÓN ---
EMAIL_USUARIO = "kiritokayabaki@gmail.com" 
EMAIL_PASSWORD = "wkpn qayc mtqj ucut"

# --- FUNCIONES DE OPTIMIZADAS ---
def leer_correos_silencioso():
    """Conexión rápida a Gmail"""
    try:
        imap = imaplib.IMAP4_SSL("imap.gmail.com")
        imap.login(EMAIL_USUARIO, EMAIL_PASSWORD)
        imap.select("INBOX", readonly=True) # Modo lectura rápida
        status, mensajes = imap.search(None, 'ALL')
        ids = mensajes[0].split()
        lista = []
        # Solo procesamos los últimos 8 para máxima velocidad
        for i in reversed(ids[-8:]):
            msg_id = i.decode() 
            res, msg = imap.fetch(i, "(RFC822)")
            for respuesta in msg:
                if isinstance(respuesta, tuple):
                    mensaje = email.message_from_bytes(respuesta[1])
                    asunto_raw = decode_header(mensaje["Subject"])[0]
                    asunto = str(asunto_raw[0])
                    # Simplificamos decodificación para evitar retrasos
                    lista.append({"id": msg_id, "Asunto": asunto, "De": mensaje.get("From")})
        imap.logout()
        return lista
    except: return None

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Gestión Maquinaria Ultra", layout="wide")

# Inicializar memoria persistente
if "db_comentarios" not in st.session_state:
    st.session_state.db_comentarios = {}
if "lista_correos" not in st.session_state:
    st.session_state.lista_correos = leer_correos_silencioso()

# --- FRAGMENTO ANTI-PARPADEO ---
@st.fragment(run_every="20s")
def zona_correos():
    # 1. Buscamos correos pero no bloqueamos la pantalla
    nuevos_datos = leer_correos_silencioso()
    if nuevos_datos:
        st.session_state.lista_correos = nuevos_datos

    # 2. Renderizamos la interfaz
    if st.session_state.lista_correos:
        for item in st.session_state.lista_correos:
            uid = item['id']
            # Usamos un contenedor con borde para que se vea más limpio
            with st.container(border=True):
                col_info, col_registro = st.columns([1, 1])
                
                with col_info:
                    st.markdown(f"### 📋 {item['Asunto']}")
                    st.caption(f"De: {item['De']}")
                
                with col_registro:
                    # Recuperar datos sin que parpadeen
                    v_previo = st.session_state.db_comentarios.get(uid, "")
                    nuevo_txt = st.text_area("Notas:", value=v_previo, key=f"t_{uid}", height=80)
                    
                    if nuevo_txt != v_previo:
                        st.session_state.db_comentarios[uid] = nuevo_txt

                    if st.session_state.db_comentarios.get(uid, "").strip():
                        st.success("🟢 ATENDIDA")
                    else:
                        st.error("🔴 PENDIENTE")
                    
                    c1, c2 = st.columns(2)
                    with c1: st.file_uploader("🖼️ Antes", key=f"a_{uid}")
                    with c2: st.file_uploader("📸 Después", key=f"d_{uid}")

# --- CUERPO PRINCIPAL ---
st.title("🚜 Control de Maquinaria")
st.markdown("---")

# Ejecutar la zona de correos
zona_correos()
