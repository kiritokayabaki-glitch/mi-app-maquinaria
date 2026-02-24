import streamlit as st
from streamlit_gsheets import GSheetsConnection
import imaplib
import email
from email.header import decode_header
import plotly.graph_objects as go
import pandas as pd

# =========================================================
# 1. CONFIGURACIÓN Y LIMPIEZA AUTOMÁTICA
# =========================================================
ID_HOJA_CALCULO = "1fdCf2HsS8KKkuqrJ8DwiDednW8lwnz7-WfvuVJwQnBo" 

st.set_page_config(page_title="Gestión Maquinaria Pro", layout="wide")

def conectar_limpio():
    try:
        # Intentamos la conexión estándar
        return st.connection("gsheets", type=GSheetsConnection)
    except Exception as e:
        st.error(f"❌ Error de llave PEM: {e}")
        st.info("Revisa que en Secrets no haya puntos (.) o espacios donde no deben ir.")
        return None

conn = conectar_limpio()

def cargar_datos_nube():
    if conn is None: return pd.DataFrame()
    try:
        return conn.read(spreadsheet=ID_HOJA_CALCULO, worksheet="Sheet1", ttl=0)
    except Exception as e:
        st.warning("Conexión lograda, pero no se pudo leer la hoja. ¿Está compartida con el Service Account?")
        return pd.DataFrame()

def guardar_datos_nube(df_nuevo):
    if conn is None: return
    try:
        conn.update(spreadsheet=ID_HOJA_CALCULO, worksheet="Sheet1", data=df_nuevo)
        st.success("✅ ¡Actualizado en Google Sheets!")
    except Exception as e:
        st.error(f"Error al guardar: {e}")

# =========================================================
# 2. MOTOR DE GMAIL
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
                    lista.append({"id": i, "asunto": asunto, "de": mensaje.get("From"), "comentario": ""})
        imap.logout()
        return lista
    except: return []

# =========================================================
# 3. INTERFAZ
# =========================================================
if conn:
    if "seccion" not in st.session_state: st.session_state.seccion = "Inicio"

    @st.fragment(run_every="30s")
    def motor_sincronizacion():
        df_actual = cargar_datos_nube()
        if not df_actual.empty:
            ids_recientes = buscar_ids_recientes()
            ids_en_nube = df_actual['id'].astype(str).tolist()
            ids_nuevos = [i for i in ids_recientes if str(i) not in ids_en_nube]
            
            if ids_nuevos:
                nuevos = leer_correos(ids_nuevos)
                df_final = pd.concat([pd.DataFrame(nuevos), df_actual], ignore_index=True)
                guardar_datos_nube(df_final)
                st.rerun()
        st.session_state.datos_app = df_actual

    motor_sincronizacion()

    df = st.session_state.get('datos_app', pd.DataFrame())

    if not df.empty:
        df['comentario'] = df['comentario'].fillna("")
        pendientes = df[df['comentario'] == ""]
        atendidas = df[df['comentario'] != ""]

        with st.sidebar:
            st.title("🚜 Panel")
            if st.button("🏠 Inicio"): st.session_state.seccion = "Inicio"
            if st.button(f"🔴 Pendientes ({len(pendientes)})"): st.session_state.seccion = "Pendientes"
            if st.button(f"🟢 Atendidas ({len(atendidas)})"): st.session_state.seccion = "Atendidas"

        if st.session_state.seccion == "Inicio":
            st.title("📊 Monitor")
            st.metric("Pendientes", len(pendientes))
            st.metric("Atendidas", len(atendidas))

        elif st.session_state.seccion == "Pendientes":
            for idx, row in pendientes.iterrows():
                with st.expander(f"Reporte: {row['asunto']}"):
                    nota = st.text_area("Solución:", key=f"n_{row['id']}")
                    if st.button("Guardar ✅", key=f"b_{row['id']}"):
                        df.loc[df['id'] == row['id'], 'comentario'] = nota
                        guardar_datos_nube(df)
                        st.rerun()
    else:
        st.info("Conectado. Esperando datos del Excel o correos nuevos...")
else:
    st.warning("⚠️ Error en Secrets. La aplicación no puede iniciar sin una llave válida.")
