import streamlit as st
from streamlit_gsheets import GSheetsConnection
import imaplib
import email
from email.header import decode_header
import plotly.graph_objects as go
import pandas as pd

# =========================================================
# 1. CONFIGURACIÓN DE CONEXIÓN FORZADA
# =========================================================
# Tu ID de hoja extraído de la URL
ID_HOJA_CALCULO = "1fdCf2HsS8KKkuqrJ8DwiDednW8lwnz7-WfvuVJwQnBo" 

# Forzamos la conexión para que use los Secrets del bloque [connections.gsheets]
conn = st.connection("gsheets", type=GSheetsConnection)

def cargar_datos_nube():
    try:
        # Forzamos modo privado con el ID
        return conn.read(spreadsheet=ID_HOJA_CALCULO, worksheet="Sheet1", ttl=0)
    except Exception:
        return pd.DataFrame(columns=["id", "asunto", "de", "cuerpo", "comentario"])

def guardar_datos_nube(df_nuevo):
    try:
        # Esta es la función que daba el error "Public Spreadsheet". 
        # Al usar el ID y la conexión mapeada, se activa el modo Editor.
        conn.update(spreadsheet=ID_HOJA_CALCULO, worksheet="Sheet1", data=df_nuevo)
        st.success("✅ ¡Base de datos actualizada!")
    except Exception as e:
        st.error(f"Error crítico de permisos: {e}")
        st.info("Verifica: 1. Secrets bloque [connections.gsheets]. 2. Correo Service Account como EDITOR en el Excel.")

# =========================================================
# 2. MOTOR DE GMAIL
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
# 3. INTERFAZ Y LÓGICA DE CONTROL
# =========================================================
st.set_page_config(page_title="Maquinaria Dash Pro", layout="wide")

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
        st.toast("🚜 Nuevo reporte detectado", icon="📥")
        st.rerun()
    
    st.session_state.datos_app = df_actual

motor_sincronizacion()

# --- VISTAS ---
df = st.session_state.get('datos_app', pd.DataFrame(columns=["id", "asunto", "de", "cuerpo", "comentario"]))
df['comentario'] = df['comentario'].fillna("")
pendientes = df[df['comentario'] == ""]
atendidas = df[df['comentario'] != ""]

with st.sidebar:
    st.title("🚜 Panel")
    if st.button("🏠 Inicio"): st.session_state.seccion = "Inicio"
    if st.button(f"🔴 Pendientes ({len(pendientes)})"): st.session_state.seccion = "Pendientes"
    if st.button(f"🟢 Atendidas ({len(atendidas)})"): st.session_state.seccion = "Atendidas"

if st.session_state.seccion == "Inicio":
    st.title("📊 Monitor de Maquinaria")
    c1, c2 = st.columns(2)
    c1.metric("Pendientes", len(pendientes))
    c2.metric("Atendidas", len(atendidas))
    if not df.empty:
        fig = go.Figure(data=[go.Pie(labels=['Pendientes', 'Atendidas'], values=[len(pendientes), len(atendidas)], hole=.4)])
        st.plotly_chart(fig)

elif st.session_state.seccion == "Pendientes":
    for index, row in pendientes.iterrows():
        uid = str(row['id'])
        with st.expander(f"⚠️ {row['asunto']}"):
            st.write(f"**De:** {row['de']}")
            st.info(row['cuerpo'])
            nota = st.text_area("Nota técnica:", key=f"n_{uid}")
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
