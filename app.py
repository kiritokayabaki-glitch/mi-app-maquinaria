import streamlit as st
from streamlit_gsheets import GSheetsConnection
import imaplib
import email
from email.header import decode_header
import plotly.graph_objects as go
import pandas as pd

# --- 1. CONEXIÓN SEGURA (USA LOS SECRETS) ---
# La conexión 'gsheets' leerá automáticamente tu bloque [gcp_service_account] de Secrets
conn = st.connection("gsheets", type=GSheetsConnection)

def cargar_datos_nube():
    try:
        # ttl=0 es CLAVE: obliga a la App a leer datos frescos de la nube cada vez
        # Asegúrate de que tu pestaña en Excel se llame exactamente "Sheet1"
        return conn.read(worksheet="Sheet1", ttl=0)
    except Exception as e:
        return pd.DataFrame(columns=["id", "asunto", "de", "cuerpo", "comentario"])

def guardar_datos_nube(df_nuevo):
    try:
        # IMPORTANTE: Eliminamos 'spreadsheet=URL_HOJA'
        # Al no poner la URL, la librería usa el permiso de Editor de tu JSON
        # para escribir directamente en la hoja vinculada a esa cuenta de servicio.
        conn.update(worksheet="Sheet1", data=df_nuevo)
    except Exception as e:
        st.error(f"Error al guardar: {e}")

# --- 2. CONFIGURACIÓN DE GMAIL Y ALERTAS ---
EMAIL_USUARIO = "kiritokayabaki@gmail.com" 
EMAIL_PASSWORD = "wkpn qayc mtqj ucut"

def play_notification_sound():
    audio_html = """<audio autoplay><source src="https://raw.githubusercontent.com/fernandoalonso-ds/sounds/main/notification.mp3" type="audio/mp3"></audio>"""
    st.components.v1.html(audio_html, height=0)

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
        ids = [i.decode() for i in mensajes[0].split()]
        imap.logout()
        return ids[-20:]
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
                        "asunto": asunto, 
                        "de": mensaje.get("From"), 
                        "cuerpo": obtener_cuerpo(mensaje)
                    })
        imap.logout()
        return lista
    except: return []

# --- 3. DISEÑO Y ESTILOS ---
st.set_page_config(page_title="Maquinaria Dash Pro", layout="wide")

st.markdown("""<style>
    .stButton > button { width: 100%; border-radius: 8px; height: 3.5em; font-weight: 600; }
    .badge-container { display: flex; justify-content: space-between; margin-top: -48px; margin-bottom: 20px; padding: 0 15px; pointer-events: none; }
    .badge-text { font-weight: bold; padding: 2px 10px; border-radius: 12px; font-size: 14px; color: #1f1f1f; }
    .bg-pendientes { background-color: #ffc1c1; }
    .bg-atendidas { background-color: #c1f2c1; }
</style>""", unsafe_allow_html=True)

if "seccion" not in st.session_state: st.session_state.seccion = "Inicio"

# --- 4. MOTOR DE SINCRONIZACIÓN (FRAGMENTO) ---
@st.fragment(run_every="10s")
def motor_sincronizacion():
    df_actual = cargar_datos_nube()
    
    # Revisar Gmail
    ids_recientes = buscar_ids_recientes()
    ids_en_nube = df_actual['id'].astype(str).tolist() if not df_actual.empty else []
    ids_nuevos = [i for i in ids_recientes if str(i) not in ids_en_nube]
    
    if ids_nuevos:
        nuevos_correos = leer_contenido_completo(ids_nuevos)
        df_nuevos = pd.DataFrame(nuevos_correos)
        df_nuevos['comentario'] = ""
        df_final = pd.concat([df_nuevos, df_actual], ignore_index=True)
        guardar_datos_nube(df_final)
        play_notification_sound()
        st.toast("🚜 Nuevo reporte en la nube", icon="📥")
        st.rerun()
    
    st.session_state.datos_app = df_actual

motor_sincronizacion()

# --- 5. INTERFAZ ---
df = st.session_state.get('datos_app', pd.DataFrame(columns=["id", "asunto", "de", "cuerpo", "comentario"]))
df['comentario'] = df['comentario'].fillna("")
pendientes = df[df['comentario'] == ""]
atendidas = df[df['comentario'] != ""]

with st.sidebar:
    st.title("🚜 Control")
    if st.button("🏠 Inicio", key="nav_i"): st.session_state.seccion = "Inicio"
    st.write("---")
    if st.button("🔴 Pendientes", key="nav_p"): st.session_state.seccion = "Pendientes"
    st.markdown(f'<div class="badge-container"><span></span><span class="badge-text bg-pendientes">{len(pendientes)}</span></div>', unsafe_allow_html=True)
    if st.button("🟢 Atendidas", key="nav_a"): st.session_state.seccion = "Atendidas"
    st.markdown(f'<div class="badge-container"><span></span><span class="badge-text bg-atendidas">{len(atendidas)}</span></div>', unsafe_allow_html=True)

if st.session_state.seccion == "Inicio":
    st.title("📊 Monitor de Maquinaria")
    c1, c2, c3 = st.columns([1,1,2])
    c1.metric("Pendientes", len(pendientes))
    c2.metric("Atendidas", len(atendidas))
    with c3:
        if not df.empty:
            fig = go.Figure(data=[go.Pie(labels=['Pendientes', 'Atendidas'], values=[len(pendientes), len(atendidas)], hole=.4, marker_colors=['#ffc1c1', '#c1f2c1'])])
            fig.update_layout(height=250, margin=dict(t=0,b=0,l=0,r=0))
            st.plotly_chart(fig, use_container_width=True)

elif st.session_state.seccion == "Pendientes":
    for index, row in pendientes.iterrows():
        uid = str(row['id'])
        with st.expander(f"⚠️ {row['asunto']}"):
            st.write(f"**De:** {row['de']}")
            st.info(row['cuerpo'])
            nota = st.text_area("Solución:", key=f"n_{uid}")
            if st.button("Confirmar ✅", key=f"btn_{uid}"):
                if nota.strip():
                    df.loc[df['id'].astype(str) == uid, 'comentario'] = nota
                    guardar_datos_nube(df)
                    st.rerun()

elif st.session_state.seccion == "Atendidas":
    for index, row in atendidas.iterrows():
        uid = str(row['id'])
        with st.expander(f"✅ {row['asunto']}"):
            st.write(f"**De:** {row['de']}")
            st.success(f"**Nota:** {row['comentario']}")
            if st.button("Reabrir 🔓", key=f"re_{uid}"):
                df.loc[df['id'].astype(str) == uid, 'comentario'] = ""
                guardar_datos_nube(df)
                st.rerun()
