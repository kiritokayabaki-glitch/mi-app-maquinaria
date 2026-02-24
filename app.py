import streamlit as st
import imaplib
import email
from email.header import decode_header
import plotly.graph_objects as go
import json
import os

# --- 1. CONFIGURACIÓN DE MEMORIA PERMANENTE ---
DB_FILE = "historial_maquinaria.json"

def guardar_en_disco():
    datos = {
        "comentarios": st.session_state.db_comentarios,
        "ids_procesados": list(st.session_state.ids_procesados),
        "lista_correos": st.session_state.lista_correos
    }
    with open(DB_FILE, "w") as f:
        json.dump(datos, f)

def cargar_de_disco():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                datos = json.load(f)
                st.session_state.db_comentarios = datos.get("comentarios", {})
                st.session_state.ids_procesados = set(datos.get("ids_procesados", []))
                st.session_state.lista_correos = datos.get("lista_correos", [])
        except: pass

# --- 2. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Maquinaria Dash Pro", layout="wide")

if "db_comentarios" not in st.session_state:
    cargar_de_disco()
    if "db_comentarios" not in st.session_state:
        st.session_state.db_comentarios = {}
        st.session_state.db_fotos = {}
        st.session_state.lista_correos = []
        st.session_state.ids_procesados = set()

if "db_fotos" not in st.session_state: st.session_state.db_fotos = {}
if "seccion" not in st.session_state: st.session_state.seccion = "Inicio"

# --- 3. CONFIGURACIÓN DE CORREO Y SONIDO ---
EMAIL_USUARIO = "kiritokayabaki@gmail.com" 
EMAIL_PASSWORD = "wkpn qayc mtqj ucut"

def play_notification_sound():
    audio_html = """<audio autoplay><source src="https://raw.githubusercontent.com/fernandoalonso-ds/sounds/main/notification.mp3" type="audio/mp3"></audio>"""
    st.components.v1.html(audio_html, height=0)

# (Funciones de Gmail idénticas a las anteriores)
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

# --- 4. MOTOR DE SINCRONIZACIÓN TOTAL (PC + CELULAR + GMAIL) ---
@st.fragment(run_every="30s")
def motor_principal():
    # A. Revisar cambios de otro dispositivo (PC <-> Celular)
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                datos_disco = json.load(f)
                # Si el archivo tiene info distinta a la memoria actual, sincronizar
                if len(datos_disco.get("comentarios", {})) != len(st.session_state.db_comentarios) or \
                   len(datos_disco.get("lista_correos", [])) != len(st.session_state.lista_correos):
                    st.session_state.db_comentarios = datos_disco.get("comentarios", {})
                    st.session_state.ids_procesados = set(datos_disco.get("ids_procesados", []))
                    st.session_state.lista_correos = datos_disco.get("lista_correos", [])
                    st.rerun()
        except: pass

    # B. Revisar correos nuevos en Gmail
    ids_recientes = buscar_ids_recientes()
    ids_nuevos = [i for i in ids_recientes if i not in st.session_state.ids_procesados]
    
    if ids_nuevos:
        nuevos_correos = leer_contenido_completo(ids_nuevos)
        st.session_state.lista_correos = nuevos_correos + st.session_state.lista_correos
        for i in ids_nuevos:
            st.session_state.ids_procesados.add(i)
        guardar_en_disco()
        st.toast(f"Nuevo: {nuevos_correos[0]['Asunto']}", icon="🔔")
        play_notification_sound()
        st.rerun()

motor_principal()

# --- 5. INTERFAZ Y DISEÑO ---
st.markdown("""<style>
    .stButton > button { width: 100%; border-radius: 8px; height: 3.5em; font-weight: 600; }
    .badge-container { display: flex; justify-content: space-between; margin-top: -48px; margin-bottom: 20px; padding: 0 15px; pointer-events: none; }
    .badge-text { font-weight: bold; padding: 2px 10px; border-radius: 12px; font-size: 14px; color: #1f1f1f; }
    .bg-pendientes { background-color: #ffc1c1; }
    .bg-atendidas { background-color: #c1f2c1; }
</style>""", unsafe_allow_html=True)

pendientes = [c for c in st.session_state.lista_correos if not st.session_state.db_comentarios.get(c['id'], "").strip()]
atendidas = [c for c in st.session_state.lista_correos if st.session_state.db_comentarios.get(c['id'], "").strip()]

with st.sidebar:
    st.markdown("### 🚜 Menú")
    if st.button("🏠 Inicio", key="nav_home"): st.session_state.seccion = "Inicio"
    if st.button("🔔 Habilitar Alertas"): st.success("Alerta sonora lista")
    st.write("---")
    if st.button("🔴 Pendientes", key="nav_p"): st.session_state.seccion = "Pendientes"
    st.markdown(f'<div class="badge-container"><span></span><span class="badge-text bg-pendientes">{len(pendientes)}</span></div>', unsafe_allow_html=True)
    if st.button("🟢 Atendidas", key="nav_a"): st.session_state.seccion = "Atendidas"
    st.markdown(f'<div class="badge-container"><span></span><span class="badge-text bg-atendidas">{len(atendidas)}</span></div>', unsafe_allow_html=True)

if st.session_state.seccion == "Inicio":
    st.title("📊 Resumen")
    c1, c2, c3 = st.columns([1,1,2])
    c1.metric("🔴 Pendientes", len(pendientes))
    c2.metric("🟢 Atendidas", len(atendidas))
    with c3:
        if st.session_state.lista_correos:
            fig = go.Figure(data=[go.Pie(labels=['Pendientes', 'Atendidas'], values=[len(pendientes), len(atendidas)], hole=.4, marker_colors=['#ffc1c1', '#c1f2c1'], pull=[0.1, 0])])
            fig.update_layout(height=250, margin=dict(t=0,b=0,l=0,r=0))
            st.plotly_chart(fig, use_container_width=True)

elif st.session_state.seccion == "Pendientes":
    st.title("🔴 Por Atender")
    for item in pendientes:
        uid = item['id']
        with st.expander(f"⚠️ {item['Asunto']}"):
            st.write(f"**De:** {item['De']}")
            st.info(item['Cuerpo'])
            coment = st.text_area("Nota:", key=f"t_{uid}")
            col1, col2 = st.columns(2)
            with col1:
                ant = st.file_uploader("Antes", key=f"a_{uid}", label_visibility="collapsed")
                if ant: st.image(ant, width=250); st.session_state.db_fotos[f"ant_{uid}"] = ant
            with col2:
                act = st.file_uploader("Actual", key=f"c_{uid}", label_visibility="collapsed")
                if act: st.image(act, width=250); st.session_state.db_fotos[f"act_{uid}"] = act
            if st.button("Confirmar ✅", key=f"b_{uid}"):
                if coment.strip():
                    st.session_state.db_comentarios[uid] = coment
                    guardar_en_disco()
                    st.rerun()

elif st.session_state.seccion == "Atendidas":
    st.title("🟢 Historial")
    for item in atendidas:
        uid = item['id']
        with st.expander(f"✅ {item['Asunto']}"):
            st.write(f"**De:** {item['De']}")
            st.info(item['Cuerpo'])
            st.success(f"Nota: {st.session_state.db_comentarios.get(uid)}")
            c1, c2 = st.columns(2)
            if f"ant_{uid}" in st.session_state.db_fotos:
                with c1: st.image(st.session_state.db_fotos[f"ant_{uid}"], width=200)
            if f"act_{uid}" in st.session_state.db_fotos:
                with c2: st.image(st.session_state.db_fotos[f"act_{uid}"], width=200)
            if st.button("Reabrir 🔓", key=f"r_{uid}"):
                st.session_state.db_comentarios.pop(uid)
                guardar_en_disco()
                st.rerun()
