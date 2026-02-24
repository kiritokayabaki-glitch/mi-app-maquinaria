import streamlit as st
import imaplib
import email
from email.header import decode_header

# --- CONFIGURACIÓN ---
EMAIL_USUARIO = "kiritokayabaki@gmail.com" 
EMAIL_PASSWORD = "wkpn qayc mtqj ucut"

# --- FUNCIONES DE DATOS (Mantenemos las anteriores) ---
def buscar_ids_recientes():
    try:
        imap = imaplib.IMAP4_SSL("imap.gmail.com")
        imap.login(EMAIL_USUARIO, EMAIL_PASSWORD)
        imap.select("INBOX", readonly=True)
        status, mensajes = imap.search(None, 'ALL')
        ids = mensajes[0].split()
        return [i.decode() for i in ids[-15:]] # Aumentamos a 15 para tener más datos
    except: return []

def leer_contenido_completo(ids_a_buscar):
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
                    asunto_raw = decode_header(mensaje.get("Subject", "Sin Asunto"))[0]
                    asunto = str(asunto_raw[0])
                    lista.append({"id": i, "Asunto": asunto, "De": mensaje.get("From")})
        imap.logout()
        return lista
    except: return []

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Maquinaria Dash Pro", layout="wide")

# Estilo CSS para imitar la imagen que subiste
st.markdown("""
    <style>
    .stButton > button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #f0f2f6;
        border: none;
        text-align: left;
        padding-left: 20px;
    }
    .badge {
        float: right;
        background-color: #e0e0e0;
        color: #31333F;
        padding: 2px 8px;
        border-radius: 10px;
        font-weight: bold;
        font-size: 0.8em;
        margin-top: 2px;
    }
    </style>
    """, unsafe_allow_html=True)

# Inicializar memoria
if "db_comentarios" not in st.session_state:
    st.session_state.db_comentarios = {}
if "lista_correos" not in st.session_state:
    st.session_state.lista_correos = leer_contenido_completo(buscar_ids_recientes())
if "seccion" not in st.session_state:
    st.session_state.seccion = "Inicio"

# Fragmento para actualización silenciosa
@st.fragment(run_every="30s")
def auto_sync():
    ids = buscar_ids_recientes()
    # Solo actualizamos si hay correos nuevos
    actuales = [c['id'] for c in st.session_state.lista_correos]
    if any(i not in actuales for i in ids):
        st.session_state.lista_correos = leer_contenido_completo(ids)
        st.rerun()

auto_sync()

# --- LÓGICA DE FILTROS ---
pendientes = [c for c in st.session_state.lista_correos if not st.session_state.db_comentarios.get(c['id'], "").strip()]
atendidas = [c for c in st.session_state.lista_correos if st.session_state.db_comentarios.get(c['id'], "").strip()]

# --- BARRA LATERAL ESTILO "APP" ---
with st.sidebar:
    st.title("🚜 Menú")
    
    # Botón Inicio
    if st.button("🏠 Inicio"):
        st.session_state.seccion = "Inicio"
    
    # Botón Pendientes con contador (Estilo tu imagen)
    # Usamos markdown para el texto con badge
    label_pend = f"🔴 Pendientes <span class='badge'>{len(pendientes)}</span>"
    if st.button("🔴 Pendientes", key="btn_p"):
        st.session_state.seccion = "Pendientes"
    st.markdown(f"<div style='margin-top:-45px; margin-bottom:20px; pointer-events:none;'>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; <span style='float:right; background:#f8d7da; padding:2px 10px; border-radius:10px;'>{len(pendientes)}</span></div>", unsafe_allow_html=True)

    # Botón Atendidas con contador
    if st.button("🟢 Atendidas", key="btn_a"):
        st.session_state.seccion = "Atendidas"
    st.markdown(f"<div style='margin-top:-45px; margin-bottom:20px; pointer-events:none;'>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; <span style='float:right; background:#d4edda; padding:2px 10px; border-radius:10px;'>{len(atendidas)}</span></div>", unsafe_allow_html=True)

# --- PANTALLAS ---
if st.session_state.seccion == "Inicio":
    st.title("📊 Resumen de Notificaciones")
    c1, c2 = st.columns(2)
    c1.metric("Por Atender", len(pendientes), delta_color="inverse")
    c2.metric("Completadas", len(atendidas))
    
    st.info("Selecciona una categoría en el menú de la izquierda para comenzar a trabajar.")

elif st.session_state.seccion == "Pendientes":
    st.title("🔴 Notificaciones Pendientes")
    for item in pendientes:
        with st.container(border=True):
            col1, col2 = st.columns([1, 1])
            with col1:
                st.subheader(item['Asunto'])
                st.write(f"De: {item['De']}")
            with col2:
                coment = st.text_area("Comentario de atención", key=f"input_{item['id']}")
                if st.button("Confirmar Atención ✅", key=f"save_{item['id']}"):
                    if coment.strip():
                        st.session_state.db_comentarios[item['id']] = coment
                        st.success("¡Atendida!")
                        st.rerun()
                    else:
                        st.warning("Escribe un comentario primero.")

elif st.session_state.seccion == "Atendidas":
    st.title("🟢 Notificaciones Atendidas")
    for item in atendidas:
        with st.expander(f"✅ {item['Asunto']}"):
            st.write(f"**Atendido el:** {st.session_state.db_comentarios.get(item['id'])}")
            st.button("Reabrir Notificación 🔓", key=f"reopen_{item['id']}", on_click=lambda id=item['id']: st.session_state.db_comentarios.pop(id))
