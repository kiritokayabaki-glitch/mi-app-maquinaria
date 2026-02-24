import streamlit as st
import imaplib
import email
from email.header import decode_header

# --- CONFIGURACIÓN ---
EMAIL_USUARIO = "kiritokayabaki@gmail.com" 
EMAIL_PASSWORD = "wkpn qayc mtqj ucut"

# --- FUNCIÓN DE CARGA ULTRA RÁPIDA ---
def buscar_ids_recientes():
    """Solo busca los IDs de los correos, que es lo más ligero"""
    try:
        imap = imaplib.IMAP4_SSL("imap.gmail.com")
        imap.login(EMAIL_USUARIO, EMAIL_PASSWORD)
        imap.select("INBOX", readonly=True)
        status, mensajes = imap.search(None, 'ALL')
        ids = mensajes[0].split()
        ultimos_ids = [i.decode() for i in ids[-8:]]
        imap.logout()
        return ultimos_ids
    except:
        return []

def leer_contenido_completo(ids_a_buscar):
    """Solo descarga el contenido si los IDs cambiaron"""
    try:
        imap = imaplib.IMAP4_SSL("imap.gmail.com")
        imap.login(EMAIL_USUARIO, EMAIL_PASSWORD)
        imap.select("INBOX", readonly=True)
        lista = []
        for i in reversed(ids_a_buscar):
            res, msg = imap.fetch(i, "(RFC822)")
            for respuesta in msg:
                if isinstance(respuesta, tuple):
                    mensaje = email.message_from_bytes(respuesta[1])
                    asunto_raw = decode_header(mensaje["Subject"])[0]
                    asunto = str(asunto_raw[0])
                    lista.append({"id": i, "Asunto": asunto, "De": mensaje.get("From")})
        imap.logout()
        return lista
    except:
        return []

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Maquinaria Pro", layout="wide")

# Inicializar memoria
if "db_comentarios" not in st.session_state:
    st.session_state.db_comentarios = {}
if "ids_actuales" not in st.session_state:
    st.session_state.ids_actuales = []
if "lista_correos" not in st.session_state:
    st.session_state.lista_correos = []

# --- LÓGICA DE ACTUALIZACIÓN INVISIBLE ---
@st.fragment(run_every="15s")
def sincronizador_invisible():
    # Paso 1: Solo pedimos los IDs (esto no se ve en pantalla)
    nuevos_ids = buscar_ids_recientes()
    
    # Paso 2: COMPARACIÓN CRÍTICA
    # Solo si los IDs son diferentes a los que ya tenemos, actualizamos la lista
    if nuevos_ids != st.session_state.ids_actuales:
        st.session_state.ids_actuales = nuevos_ids
        st.session_state.lista_correos = leer_contenido_completo(nuevos_ids)
        st.rerun() # Solo reinicia la app si HAY un correo nuevo de verdad

# --- INTERFAZ FIJA (NUNCA PARPADEA) ---
st.title("🚜 Control de Maquinaria")
st.caption("Estado: Protegido contra parpadeo")

# Ejecutar sincronizador en segundo plano
sincronizador_invisible()

# Mostrar la información que ya está en memoria
if st.session_state.lista_correos:
    for item in st.session_state.lista_correos:
        uid = item['id']
        with st.container(border=True):
            col1, col2 = st.columns([1, 1])
            with col1:
                st.subheader(item['Asunto'])
                st.write(f"De: {item['De']}")
            with col2:
                v_previo = st.session_state.db_comentarios.get(uid, "")
                nuevo_txt = st.text_area("Notas:", value=v_previo, key=f"t_{uid}")
                
                if nuevo_txt != v_previo:
                    st.session_state.db_comentarios[uid] = nuevo_txt

                if st.session_state.db_comentarios.get(uid, "").strip():
                    st.success("🟢 ATENDIDA")
                else:
                    st.error("🔴 PENDIENTE")
                
                c1, c2 = st.columns(2)
                with c1: st.file_uploader("🖼️ Antes", key=f"a_{uid}")
                with c2: st.file_uploader("📸 Después", key=f"d_{uid}")
