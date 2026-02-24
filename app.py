import streamlit as st
from streamlit_gsheets import GSheetsConnection
import imaplib
import email
from email.header import decode_header
import plotly.graph_objects as go
import pandas as pd
import re

# =========================================================
# 1. CONFIGURACIÓN Y LIMPIEZA DE CONEXIÓN
# =========================================================
ID_HOJA_CALCULO = "1fdCf2HsS8KKkuqrJ8DwiDednW8lwnz7-WfvuVJwQnBo" 

def obtener_conexion():
    try:
        # Intentamos conectar usando el bloque [connections.gsheets] de los Secrets
        return st.connection("gsheets", type=GSheetsConnection)
    except Exception as e:
        st.error(f"❌ Error al configurar la conexión: {e}")
        return None

conn = obtener_conexion()

def cargar_datos_nube():
    if conn is None: return pd.DataFrame()
    try:
        return conn.read(spreadsheet=ID_HOJA_CALCULO, worksheet="Sheet1", ttl=0)
    except Exception as e:
        st.error(f"❌ Error al leer la hoja: {e}")
        return pd.DataFrame()

def guardar_datos_nube(df_nuevo):
    if conn is None: return
    try:
        conn.update(spreadsheet=ID_HOJA_CALCULO, worksheet="Sheet1", data=df_nuevo)
        st.success("✅ ¡Base de datos sincronizada!")
    except Exception as e:
        st.error(f"❌ Error al guardar: {e}")

# =========================================================
# 2. MOTOR DE GMAIL (RECEPCIÓN DE REPORTES)
# =========================================================
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
        return ids[-10:] # Solo los últimos 10 correos
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
                    asunto = asunto_raw[0].decode(asunto_raw[1] or "utf-8") if isinstance(asunto_raw[0], bytes) else asunto_raw[0]
                    lista.append({
                        "id": i, 
                        "asunto": asunto, 
                        "de": mensaje.get("From"), 
                        "comentario": ""
                    })
        imap.logout()
        return lista
    except: return []

# =========================================================
# 3. INTERFAZ Y LÓGICA DE CONTROL
# =========================================================
st.set_page_config(page_title="Gestión Maquinaria Pro", layout="wide")

if "seccion" not in st.session_state: st.session_state.seccion = "Inicio"

# Motor de sincronización automática cada 20 segundos
@st.fragment(run_every="20s")
def motor_sincronizacion():
    df_actual = cargar_datos_nube()
    if not df_actual.empty:
        ids_recientes = buscar_ids_recientes()
        ids_en_nube = df_actual['id'].astype(str).tolist() if not df_actual.empty else []
        ids_nuevos = [i for i in ids_recientes if str(i) not in ids_en_nube]
        
        if ids_nuevos:
            nuevos_correos = leer_contenido_completo(ids_nuevos)
            if nuevos_correos:
                df_final = pd.concat([pd.DataFrame(nuevos_correos), df_actual], ignore_index=True)
                guardar_datos_nube(df_final)
                st.rerun()
    st.session_state.datos_app = df_actual

# Solo corre el motor si la conexión fue exitosa
if conn:
    motor_sincronizacion()

# Procesar datos para la interfaz
df = st.session_state.get('datos_app', pd.DataFrame())

if not df.empty:
    df['comentario'] = df['comentario'].fillna("")
    pendientes = df[df['comentario'] == ""]
    atendidas = df[df['comentario'] != ""]

    with st.sidebar:
        st.title("🚜 Control")
        if st.button("🏠 Inicio"): st.session_state.seccion = "Inicio"
        if st.button(f"🔴 Pendientes ({len(pendientes)})"): st.session_state.seccion = "Pendientes"
        if st.button(f"🟢 Atendidas ({len(atendidas)})"): st.session_state.seccion = "Atendidas"

    if st.session_state.seccion == "Inicio":
        st.title("📊 Resumen de Maquinaria")
        c1, c2 = st.columns(2)
        c1.metric("Pendientes", len(pendientes))
        c2.metric("Atendidas", len(atendidas))
        if not df.empty:
            fig = go.Figure(data=[go.Pie(labels=['Pendientes', 'Atendidas'], 
                                        values=[len(pendientes), len(atendidas)], 
                                        hole=.4)])
            st.plotly_chart(fig)

    elif st.session_state.seccion == "Pendientes":
        st.header("⚠️ Reportes por atender")
        for idx, row in pendientes.iterrows():
            with st.expander(f"Asunto: {row['asunto']}"):
                st.write(f"**De:** {row['de']}")
                nota = st.text_area("Solución:", key=f"n_{row['id']}")
                if st.button("Confirmar ✅", key=f"b_{row['id']}"):
                    df.loc[df['id'] == row['id'], 'comentario'] = nota
                    guardar_datos_nube(df)
                    st.rerun()

    elif st.session_state.seccion == "Atendidas":
        st.header("✅ Historial")
        for idx, row in atendidas.iterrows():
            with st.expander(f"Finalizado: {row['asunto']}"):
                st.success(f"**Solución:** {row['comentario']}")
else:
    if not conn:
        st.warning("⚠️ Esperando configuración correcta de Secrets...")
    else:
        st.info("Conectado a Google Sheets. Esperando que lleguen reportes al correo...")
