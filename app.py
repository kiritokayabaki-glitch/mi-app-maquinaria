import streamlit as st
import imaplib
import email
from email.header import decode_header
import plotly.graph_objects as go
import base64 # Para codificar el sonido

# --- CONFIGURACIÓN ---
EMAIL_USUARIO = "kiritokayabaki@gmail.com" 
EMAIL_PASSWORD = "wkpn qayc mtqj ucut"

# --- FUNCIÓN DE SONIDO ---
def play_notification_sound():
    # Sonido de "Ping" corto y profesional
    audio_html = """
        <audio autoplay>
            <source src="https://raw.githubusercontent.com/fernandoalonso-ds/sounds/main/notification.mp3" type="audio/mp3">
        </audio>
    """
    st.components.v1.html(audio_html, height=0)

# --- FUNCIONES DE DATOS (Sin cambios) ---
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
                    lista.append({"id": i, "Asunto": asunto, "De": mensaje.get("From"), "Cuerpo": obtener_cuerpo(mensaje)})
        imap.logout()
        return lista
    except: return []

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Maquinaria Dash Pro", layout="wide")

# --- INICIALIZACIÓN ---
if "db_comentarios" not in st.session_state: st.session_state.db_comentarios = {}
if "db_fotos" not in st.session_state: st.session_state.db_fotos = {}
if "lista_correos" not in st.session_state: st.session_state.lista_correos = []
if "ids_procesados" not in st.session_state: st.session_state.ids_procesados = set()
if "seccion" not in st.session_state: st.session_state.seccion = "Inicio"
if "alerta_nueva" in st.session_state: # Control de notificación visual
    st.toast(st.session_state.alerta_nueva, icon="🔔")
    del st.session_state.alerta_nueva

# --- MOTOR DE ACTUALIZACIÓN CON NOTIFICACIÓN ---
@st.fragment(run_every="30s")
def sincronizador_con_audio():
    ids_recientes = buscar_ids_recientes()
    ids_nuevos = [i for i in ids_recientes if i not in st.session_state.ids_procesados]
    
    if ids_nuevos:
        nuevos_correos = leer_contenido_completo(ids_nuevos)
        # Tomamos el asunto del correo más reciente para la alerta
        asunto_alerta = nuevos_correos[0]['Asunto']
        
        # Guardamos en lista
        ids_en_lista = [c['id'] for c in st.session_state.lista_correos]
        correos_reales = [c for c in nuevos_correos if c['id'] not in ids_en_lista]
        st.session_state.lista_correos = correos_reales + st.session_state.lista_correos
        
        for i in ids_nuevos:
            st.session_state.ids_procesados.add(i)
        
        # DISPARAR ALERTAS
        st.session_state.alerta_nueva = f"Nuevo correo: {asunto_alerta}"
        play_notification_sound()
        st.rerun()

sincronizador_con_audio()

# --- CSS ---
st.markdown("""
    <style>
    .stButton > button { width: 100%; border-radius: 8px; height: 3.5em; font-weight: 600; }
    .badge-container { display: flex; justify-content: space-between; margin-top: -48px; margin-bottom: 20px; padding: 0 15px; pointer-events: none; }
    .badge-text { font-weight: bold; padding: 2px 10px; border-radius: 12px; font-size: 14px; color: #1f1f1f; }
    .bg-pendientes { background-color: #ffc1c1; }
    .bg-atendidas { background-color: #c1f2c1; }
    </style>
    """, unsafe_allow_html=True)

# Filtros
pendientes = [c for c in st.session_state.lista_correos if not st.session_state.db_comentarios.get(c['id'], "").strip()]
atendidas = [c for c in st.session_state.lista_correos if st.session_state.db_comentarios.get(c['id'], "").strip()]

# --- BARRA LATERAL ---
with st.sidebar:
    st.markdown("### 🚜 Menú")
    if st.button("🏠 Inicio", key="nav_ini"): st.session_state.seccion = "Inicio"
    
    # BOTÓN PARA ACTIVAR SONIDO (OBLIGATORIO POR EL NAVEGADOR)
    st.info("Activa las alertas sonoras:")
    if st.button("🔔 Habilitar Sonido"):
        st.success("Sonido habilitado")
    
    st.write("---")
    if st.button("🔴 Pendientes", key="nav_pend"): st.session_state.seccion = "Pendientes"
    st.markdown(f'<div class="badge-container"><span></span><span class="badge-text bg-pendientes">{len(pendientes)}</span></div>', unsafe_allow_html=True)
    if st.button("🟢 Atendidas", key="nav_atend"): st.session_state.seccion = "Atendidas"
    st.markdown(f'<div class="badge-container"><span></span><span class="badge-text bg-atendidas">{len(atendidas)}</span></div>', unsafe_allow_html=True)

# --- PANTALLAS (Resumen del código anterior) ---
if st.session_state.seccion == "Inicio":
    st.title("📊 Resumen de Tareas")
    col1, col2, col3 = st.columns([1,1,2])
    col1.metric("🔴 Pendientes", len(pendientes))
    col2.metric("🟢 Atendidas", len(atendidas))
    with col3:
        if st.session_state.lista_correos:
            fig = go.Figure(data=[go.Pie(labels=['Pendientes', 'Atendidas'], values=[len(pendientes), len(atendidas)], hole=.4, marker_colors=['#ffc1c1', '#c1f2c1'], pull=[0.1, 0])])
            fig.update_layout(height=250, margin=dict(t=0,b=0,l=0,r=0))
            st.plotly_chart(fig, use_container_width=True)

elif st.session_state.seccion == "Pendientes":
    st.title("🔴 Órdenes por Atender")
    for item in pendientes:
        with st.expander(f"⚠️ {item['Asunto']}"):
            st.write(f"**De:** {item['De']}")
            st.info(f"**Cuerpo:**\n\n{item['Cuerpo']}")
            coment = st.text_area("Nota:", key=f"t_p_{item['id']}")
            c1, c2 = st.columns(2)
            with c1:
                ant = st.file_uploader("Antes", key=f"ua_{item['id']}", label_visibility="collapsed")
                if ant: st.image(ant, width=250); st.session_state.db_fotos[f"ant_{item['id']}"] = ant
            with c2:
                act = st.file_uploader("Actual", key=f"uc_{item['id']}", label_visibility="collapsed")
                if act: st.image(act, width=250); st.session_state.db_fotos[f"act_{item['id']}"] = act
            if st.button("Confirmar ✅", key=f"b_s_{item['id']}"):
                if coment.strip(): st.session_state.db_comentarios[item['id']] = coment; st.rerun()

elif st.session_state.seccion == "Atendidas":
    st.title("🟢 Historial")
    for item in atendidas:
        with st.expander(f"✅ {item['Asunto']}"):
            st.write(f"**De:** {item['De']}")
            st.info(f"**Cuerpo:**\n\n{item['Cuerpo']}")
            st.success(f"**Nota:** {st.session_state.db_comentarios.get(item['id'])}")
            c1, c2 = st.columns(2)
            if f"ant_{item['id']}" in st.session_state.db_fotos:
                with c1: st.image(st.session_state.db_fotos[f"ant_{item['id']}"], width=200)
            if f"act_{item['id']}" in st.session_state.db_fotos:
                with c2: st.image(st.session_state.db_fotos[f"act_{item['id']}"], width=200)
            if st.button("Reabrir 🔓", key=f"b_r_{item['id']}"):
                st.session_state.db_comentarios.pop(item['id']); st.rerun()
