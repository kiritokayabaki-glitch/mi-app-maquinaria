import streamlit as st
from streamlit_gsheets import GSheetsConnection
import imaplib
import email
from email.header import decode_header
import plotly.graph_objects as go
import pandas as pd

# =========================================================
# CONFIGURACIÓN DE CONEXIÓN (ID YA CONFIGURADO)
# =========================================================
ID_HOJA_CALCULO = "1fdCf2HsS8KKkuqrJ8DwiDednW8lwnz7-WfvuVJwQnBo" 

# Creamos la conexión. Automáticamente usará [gcp_service_account] de tus Secrets.
conn = st.connection("gsheets", type=GSheetsConnection)

def cargar_datos_nube():
    try:
        # Usamos el ID para forzar el modo privado y evitar errores de permisos
        return conn.read(spreadsheet=ID_HOJA_CALCULO, worksheet="Sheet1", ttl=0)
    except Exception:
        return pd.DataFrame(columns=["id", "asunto", "de", "cuerpo", "comentario"])

def guardar_datos_nube(df_nuevo):
    try:
        # Al usar el ID, la librería sabe que debe usar la cuenta de servicio (Editor)
        conn.update(spreadsheet=ID_HOJA_CALCULO, worksheet="Sheet1", data=df_nuevo)
        st.success("✅ ¡Cambios guardados en Google Sheets!")
    except Exception as e:
        st.error(f"Error al guardar: {e}")
        st.info("Asegúrate de haber compartido el Excel como EDITOR con tu correo de service account.")

# =========================================================
# CONFIGURACIÓN DE GMAIL (ALERTAS)
# =========================================================
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

# =========================================================
# DISEÑO Y MOTOR AUTOMÁTICO
# =========================================================
st.set_page_config(page_title="Gestión Maquinaria Pro", layout="wide")

if "seccion" not in st.session_state: st.session_state.seccion = "Inicio"

@st.fragment(run_every="10s")
def motor_sincronizacion():
    df_actual = cargar_datos_nube()
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
        st.toast("🚜 Nuevo reporte recibido", icon="📥")
        st.rerun()
    
    st.session_state.datos_app = df_actual

motor_sincronizacion()

# =========================================================
# INTERFAZ VISUAL
# =========================================================
df = st.session_state.get('datos_app', pd.DataFrame(columns=["id", "asunto", "de", "cuerpo", "comentario"]))
df['comentario'] = df['comentario'].fillna("")
pendientes = df[df['comentario'] == ""]
atendidas = df[df['comentario'] != ""]

with st.sidebar:
    st.title("🚜 Control")
    if st.button("🏠 Inicio"): st.session_state.seccion = "Inicio"
    st.write("---")
    if st.button("🔴 Pendientes"): st.session_state.seccion = "Pendientes"
    st.write(f"({len(pendientes)})")
    if st.button("🟢 Atendidas"): st.session_state.seccion = "Atendidas"
    st.write(f"({len(atendidas)})")

if st.session_state.seccion == "Inicio":
    st.title("📊 Monitor de Maquinaria")
    c1, c2, c3 = st.columns([1,1,2])
    c1.metric("Pendientes", len(pendientes))
    c2.metric("Atendidas", len(atendidas))
    if not df.empty:
        with c3:
            fig = go.Figure(data=[go.Pie(labels=['Pendientes', 'Atendidas'], values=[len(pendientes), len(atendidas)], hole=.4)])
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
            st.success(f"**Solución:** {row['comentario']}")
            if st.button("Reabrir 🔓", key=f"re_{uid}"):
                df.loc[df['id'].astype(str) == uid, 'comentario'] = ""
                guardar_datos_nube(df)
                st.rerun()
