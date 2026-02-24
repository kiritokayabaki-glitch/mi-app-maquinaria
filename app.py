import streamlit as st
import imaplib
import email
from email.header import decode_header

# --- CONFIGURACIÓN ---
EMAIL_USUARIO = "kiritokayabaki@gmail.com" 
EMAIL_PASSWORD = "wkpn qayc mtqj ucut"

# --- FUNCIONES DE DATOS ---
def buscar_ids_recientes():
    try:
        imap = imaplib.IMAP4_SSL("imap.gmail.com")
        imap.login(EMAIL_USUARIO, EMAIL_PASSWORD)
        imap.select("INBOX", readonly=True)
        status, mensajes = imap.search(None, 'ALL')
        ids = mensajes[0].split()
        return [i.decode() for i in ids[-15:]]
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

# --- CSS PERSONALIZADO ---
st.markdown("""
    <style>
    .stButton > button { width: 100%; border-radius: 8px; height: 3.5em; background-color: #f0f2f6; color: #1f1f1f !important; font-weight: 600; }
    .badge-container { display: flex; justify-content: space-between; margin-top: -48px; margin-bottom: 20px; padding: 0 15px; pointer-events: none; }
    .badge-text { font-weight: bold; padding: 2px 10px; border-radius: 12px; font-size: 14px; color: #1f1f1f; }
    .bg-pendientes { background-color: #ffc1c1; }
    .bg-atendidas { background-color: #c1f2c1; }
    </style>
    """, unsafe_allow_html=True)

# Inicializar memoria
if "db_comentarios" not in st.session_state: st.session_state.db_comentarios = {}
if "db_fotos" not in st.session_state: st.session_state.db_fotos = {}
if "lista_correos" not in st.session_state: st.session_state.lista_correos = leer_contenido_completo(buscar_ids_recientes())
if "seccion" not in st.session_state: st.session_state.seccion = "Inicio"

# Filtros
pendientes = [c for c in st.session_state.lista_correos if not st.session_state.db_comentarios.get(c['id'], "").strip()]
atendidas = [c for c in st.session_state.lista_correos if st.session_state.db_comentarios.get(c['id'], "").strip()]

# --- BARRA LATERAL ---
with st.sidebar:
    st.markdown("### 🚜 Menú")
    if st.button("🏠 Inicio"): st.session_state.seccion = "Inicio"
    st.write("")
    if st.button("🔴 Pendientes"): st.session_state.seccion = "Pendientes"
    st.markdown(f'<div class="badge-container"><span></span><span class="badge-text bg-pendientes">{len(pendientes)}</span></div>', unsafe_allow_html=True)
    if st.button("🟢 Atendidas"): st.session_state.seccion = "Atendidas"
    st.markdown(f'<div class="badge-container"><span></span><span class="badge-text bg-atendidas">{len(atendidas)}</span></div>', unsafe_allow_html=True)

# --- PANTALLAS ---
if st.session_state.seccion == "Inicio":
    st.title("📊 Resumen de Tareas")
    col1, col2 = st.columns(2)
    col1.metric("Pendientes", len(pendientes))
    col2.metric("Atendidas", len(atendidas))

elif st.session_state.seccion == "Pendientes":
    st.title("🔴 Notificaciones Pendientes")
    for item in pendientes:
        uid = item['id']
        with st.expander(f"⚠️ {item['Asunto']}"):
            st.write(f"**De:** {item['De']}")
            coment = st.text_area("Registrar nota:", key=f"in_{uid}")
            
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**🖼️ Anteriormente-Imagen**")
                foto_ant = st.file_uploader("Subir antes", key=f"u_ant_{uid}", label_visibility="collapsed")
                if foto_ant:
                    # TAMAÑO AJUSTADO AQUÍ
                    st.image(foto_ant, width=250) 
                    st.session_state.db_fotos[f"ant_{uid}"] = foto_ant
            with c2:
                st.markdown("**📸 Actual-Imagen**")
                foto_act = st.file_uploader("Subir actual", key=f"u_act_{uid}", label_visibility="collapsed")
                if foto_act:
                    # TAMAÑO AJUSTADO AQUÍ
                    st.image(foto_act, width=250)
                    st.session_state.db_fotos[f"act_{uid}"] = foto_act
            
            if st.button("Confirmar Atención ✅", key=f"sv_{uid}"):
                if coment.strip():
                    st.session_state.db_comentarios[uid] = coment
                    st.rerun()

elif st.session_state.seccion == "Atendidas":
    st.title("🟢 Historial de Atendidas")
    for item in atendidas:
        uid = item['id']
        with st.expander(f"✅ {item['Asunto']}"):
            st.write(f"**Nota de atención:** {st.session_state.db_comentarios.get(uid)}")
            
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**🖼️ Vista Anterior**")
                if f"ant_{uid}" in st.session_state.db_fotos:
                    # TAMAÑO AJUSTADO AQUÍ
                    st.image(st.session_state.db_fotos[f"ant_{uid}"], width=200)
                else: st.warning("Sin foto")
            with c2:
                st.markdown("**📸 Vista Actual**")
                if f"act_{uid}" in st.session_state.db_fotos:
                    # TAMAÑO AJUSTADO AQUÍ
                    st.image(st.session_state.db_fotos[f"act_{uid}"], width=200)
                else: st.warning("Sin foto")
            
            if st.button("Reabrir Notificación 🔓", key=f"re_{uid}"):
                st.session_state.db_comentarios.pop(uid)
                st.rerun()
