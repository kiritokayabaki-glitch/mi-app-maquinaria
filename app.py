import streamlit as st
import imaplib
import email
from email.header import decode_header
import plotly.graph_objects as go

# --- CONFIGURACIÓN ---
EMAIL_USUARIO = "kiritokayabaki@gmail.com" 
EMAIL_PASSWORD = "wkpn qayc mtqj ucut"

# --- FUNCIONES DE DATOS ---
def decodificar_texto(texto, encoding):
    try:
        if isinstance(texto, bytes): return texto.decode(encoding or "utf-8", errors="replace")
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
    return cuerpo[:800]

def buscar_ids_recientes():
    try:
        imap = imaplib.IMAP4_SSL("imap.gmail.com")
        imap.login(EMAIL_USUARIO, EMAIL_PASSWORD)
        imap.select("INBOX", readonly=True)
        status, mensajes = imap.search(None, 'ALL')
        ids = mensajes[0].split()
        return [i.decode() for i in ids[-20:]]
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
                    asunto = decodificar_texto(asunto_raw[0], asunto_raw[1])
                    lista.append({
                        "id": i, 
                        "Asunto": asunto, 
                        "De": mensaje.get("From"), 
                        "Cuerpo": obtener_cuerpo(mensaje)
                    })
        imap.logout()
        return lista
    except: return []

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Maquinaria Dash Pro", layout="wide")

# --- CSS ---
st.markdown("""
    <style>
    .stButton > button { width: 100%; border-radius: 8px; height: 3.5em; background-color: #f0f2f6; color: #1f1f1f !important; font-weight: 600; }
    .badge-container { display: flex; justify-content: space-between; margin-top: -48px; margin-bottom: 20px; padding: 0 15px; pointer-events: none; }
    .badge-text { font-weight: bold; padding: 2px 10px; border-radius: 12px; font-size: 14px; color: #1f1f1f; }
    .bg-pendientes { background-color: #ffc1c1; }
    .bg-atendidas { background-color: #c1f2c1; }
    </style>
    """, unsafe_allow_html=True)

# --- INICIALIZACIÓN ---
if "db_comentarios" not in st.session_state: st.session_state.db_comentarios = {}
if "db_fotos" not in st.session_state: st.session_state.db_fotos = {}
if "lista_correos" not in st.session_state: st.session_state.lista_correos = []
if "ids_procesados" not in st.session_state: st.session_state.ids_procesados = set()
if "seccion" not in st.session_state: st.session_state.seccion = "Inicio"

# --- MOTOR DE ACTUALIZACIÓN ---
@st.fragment(run_every="30s")
def sincronizador_infinito():
    ids_recientes = buscar_ids_recientes()
    ids_nuevos = [i for i in ids_recientes if i not in st.session_state.ids_procesados]
    
    if ids_nuevos:
        nuevos_correos = leer_contenido_completo(ids_nuevos)
        # Filtro de seguridad extra para evitar duplicados en la lista visual
        ids_en_lista = [c['id'] for c in st.session_state.lista_correos]
        correos_reales = [c for c in nuevos_correos if c['id'] not in ids_en_lista]
        
        st.session_state.lista_correos = correos_reales + st.session_state.lista_correos
        for i in ids_nuevos:
            st.session_state.ids_procesados.add(i)
        st.rerun()

sincronizador_infinito()

# Filtros
pendientes = [c for c in st.session_state.lista_correos if not st.session_state.db_comentarios.get(c['id'], "").strip()]
atendidas = [c for c in st.session_state.lista_correos if st.session_state.db_comentarios.get(c['id'], "").strip()]

# --- BARRA LATERAL ---
with st.sidebar:
    st.markdown("### 🚜 Menú")
    if st.button("🏠 Inicio", key="btn_nav_inicio"): st.session_state.seccion = "Inicio"
    st.write("")
    if st.button("🔴 Pendientes", key="btn_nav_pend"): st.session_state.seccion = "Pendientes"
    st.markdown(f'<div class="badge-container"><span></span><span class="badge-text bg-pendientes">{len(pendientes)}</span></div>', unsafe_allow_html=True)
    if st.button("🟢 Atendidas", key="btn_nav_atend"): st.session_state.seccion = "Atendidas"
    st.markdown(f'<div class="badge-container"><span></span><span class="badge-text bg-atendidas">{len(atendidas)}</span></div>', unsafe_allow_html=True)

# --- PANTALLAS ---
if st.session_state.seccion == "Inicio":
    st.title("📊 Resumen de Tareas")
    col_met1, col_met2, col_graf = st.columns([1, 1, 2])
    with col_met1: st.metric("🔴 Pendientes", len(pendientes))
    with col_met2: st.metric("🟢 Atendidas", len(atendidas))
    with col_graf:
        if st.session_state.lista_correos:
            fig = go.Figure(data=[go.Pie(
                labels=['Pendientes', 'Atendidas'], 
                values=[len(pendientes), len(atendidas)],
                hole=.4, marker_colors=['#ffc1c1', '#c1f2c1'],
                pull=[0.1, 0]
            )])
            fig.update_layout(height=300, margin=dict(t=0, b=0, l=0, r=0))
            st.plotly_chart(fig, use_container_width=True)

elif st.session_state.seccion == "Pendientes":
    st.title("🔴 Órdenes por Atender")
    for item in pendientes:
        uid = item['id']
        with st.expander(f"⚠️ {item.get('Asunto')}"):
            st.write(f"**De:** {item.get('De')}")
            st.info(f"**Cuerpo:**\n\n{item.get('Cuerpo', 'Sin contenido')}")
            # LLAVES ÚNICAS POR SECCIÓN
            coment = st.text_area("Nota:", key=f"text_pend_{uid}")
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**🖼️ Antes**")
                f_ant = st.file_uploader("Subir", key=f"up_ant_pend_{uid}", label_visibility="collapsed")
                if f_ant: st.image(f_ant, width=250); st.session_state.db_fotos[f"ant_{uid}"] = f_ant
            with c2:
                st.markdown("**📸 Actual**")
                f_act = st.file_uploader("Subir", key=f"up_act_pend_{uid}", label_visibility="collapsed")
                if f_act: st.image(f_act, width=250); st.session_state.db_fotos[f"act_{uid}"] = f_act
            if st.button("Confirmar ✅", key=f"btn_save_pend_{uid}"):
                if coment.strip():
                    st.session_state.db_comentarios[uid] = coment
                    st.rerun()

elif st.session_state.seccion == "Atendidas":
    st.title("🟢 Historial Acumulado")
    for item in atendidas:
        uid = item['id']
        with st.expander(f"✅ {item.get('Asunto')}"):
            st.write(f"**De:** {item.get('De')}")
            st.info(f"**Cuerpo:**\n\n{item.get('Cuerpo', 'Sin contenido')}")
            st.success(f"**Nota:** {st.session_state.db_comentarios.get(uid)}")
            c1, c2 = st.columns(2)
            if f"ant_{uid}" in st.session_state.db_fotos:
                with c1: st.image(st.session_state.db_fotos[f"ant_{uid}"], width=200)
            if f"act_{uid}" in st.session_state.db_fotos:
                with c2: st.image(st.session_state.db_fotos[f"act_{uid}"], width=200)
            # LLAVE ÚNICA PARA EL BOTÓN DE REABRIR
            if st.button("Reabrir 🔓", key=f"btn_reopen_aten_{uid}"):
                st.session_state.db_comentarios.pop(uid)
                st.rerun()
