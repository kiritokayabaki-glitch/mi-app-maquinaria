import streamlit as st
from streamlit_gsheets import GSheetsConnection
import imaplib
import email
from email.header import decode_header
import plotly.graph_objects as go
import pandas as pd

# 1. IDENTIFICACIÓN
ID_HOJA_CALCULO = "1fdCf2HsS8KKkuqrJ8DwiDednW8lwnz7-WfvuVJwQnBo" 

# Intentar conexión robusta
try:
    if "connections" in st.secrets and "gsheets" in st.secrets.connections:
        conn = st.connection("gsheets", type=GSheetsConnection)
    else:
        st.error("❌ No se encontró el bloque [connections.gsheets] en Secrets.")
        conn = None
except Exception as e:
    st.error(f"❌ Error de formato en la llave (PEM): {e}")
    st.info("Revisa que la private_key en Secrets no tenga espacios extra y use \\n para saltos de línea.")
    conn = None

def cargar_datos_nube():
    if conn is None: return pd.DataFrame(columns=["id", "asunto", "de", "cuerpo", "comentario"])
    try:
        return conn.read(spreadsheet=ID_HOJA_CALCULO, worksheet="Sheet1", ttl=0)
    except Exception as e:
        st.warning(f"Conexión establecida pero la hoja está vacía o inaccesible: {e}")
        return pd.DataFrame(columns=["id", "asunto", "de", "cuerpo", "comentario"])

def guardar_datos_nube(df_nuevo):
    if conn is None: return
    try:
        conn.update(spreadsheet=ID_HOJA_CALCULO, worksheet="Sheet1", data=df_nuevo)
        st.success("✅ ¡Base de datos sincronizada!")
    except Exception as e:
        st.error(f"Error al guardar: {e}")

# 2. MOTOR DE GMAIL
EMAIL_USUARIO = "kiritokayabaki@gmail.com" 
EMAIL_PASSWORD = "wkpn qayc mtqj ucut"

def buscar_ids_recientes():
    try:
        imap = imaplib.IMAP4_SSL("imap.gmail.com")
        imap.login(EMAIL_USUARIO, EMAIL_PASSWORD)
        imap.select("INBOX", readonly=True)
        status, mensajes = imap.search(None, 'ALL')
        ids = [i.decode() for i in mensajes[0].split()]
        imap.logout()
        return ids[-10:]
    except: return []

def leer_correos(ids_a_buscar):
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
                    asunto = asunto_raw[0].decode(asunto_raw[1] or "utf-8") if isinstance(asunto_raw[0], bytes) else asunto_raw[0]
                    lista.append({"id": i, "asunto": asunto, "de": mensaje.get("From"), "cuerpo": "Nuevo reporte recibido", "comentario": ""})
        imap.logout()
        return lista
    except: return []

# 3. INTERFAZ
st.set_page_config(page_title="Control Maquinaria", layout="wide")

if "seccion" not in st.session_state: st.session_state.seccion = "Inicio"

@st.fragment(run_every="20s")
def motor_sincronizacion():
    df_actual = cargar_datos_nube()
    ids_recientes = buscar_ids_recientes()
    ids_en_nube = df_actual['id'].astype(str).tolist() if not df_actual.empty else []
    ids_nuevos = [i for i in ids_recientes if str(i) not in ids_en_nube]
    
    if ids_nuevos:
        nuevos = leer_correos(ids_nuevos)
        if nuevos:
            df_final = pd.concat([pd.DataFrame(nuevos), df_actual], ignore_index=True)
            guardar_datos_nube(df_final)
            st.rerun()
    st.session_state.datos_app = df_actual

motor_sincronizacion()

df = st.session_state.get('datos_app', pd.DataFrame(columns=["id", "asunto", "de", "cuerpo", "comentario"]))
pendientes = df[df['comentario'] == ""] if not df.empty else pd.DataFrame()
atendidas = df[df['comentario'] != ""] if not df.empty else pd.DataFrame()

with st.sidebar:
    st.title("🚜 Menú")
    if st.button("🏠 Inicio"): st.session_state.seccion = "Inicio"
    if st.button(f"🔴 Pendientes ({len(pendientes)})"): st.session_state.seccion = "Pendientes"
    if st.button(f"🟢 Atendidas ({len(atendidas)})"): st.session_state.seccion = "Atendidas"

if st.session_state.seccion == "Inicio":
    st.title("📊 Resumen")
    st.metric("Pendientes", len(pendientes))
    st.metric("Atendidas", len(atendidas))

elif st.session_state.seccion == "Pendientes":
    for idx, row in pendientes.iterrows():
        with st.expander(f"Reporte: {row['asunto']}"):
            txt = st.text_area("Solución:", key=f"t_{row['id']}")
            if st.button("Guardar ✅", key=f"b_{row['id']}"):
                df.loc[df['id'] == row['id'], 'comentario'] = txt
                guardar_datos_nube(df)
                st.rerun()
