import streamlit as st
from streamlit_gsheets import GSheetsConnection
import imaplib
import email
from email.header import decode_header
import pandas as pd

# =========================================================
# 1. CONFIGURACIÓN
# =========================================================
ID_HOJA_CALCULO = "1fdCf2HsS8KKkuqrJ8DwiDednW8lwnz7-WfvuVJwQnBo" 

st.set_page_config(page_title="Gestión Maquinaria Pro", layout="wide")

# Conexión directa
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    error_conexion = False
except Exception as e:
    st.error(f"❌ Error de conexión: {e}")
    error_conexion = True

def cargar_datos_nube():
    try:
        return conn.read(spreadsheet=ID_HOJA_CALCULO, worksheet="Sheet1", ttl=0)
    except:
        return pd.DataFrame()

def guardar_datos_nube(df_nuevo):
    try:
        conn.update(spreadsheet=ID_HOJA_CALCULO, worksheet="Sheet1", data=df_nuevo)
        st.success("✅ ¡Cambios guardados!")
    except Exception as e:
        st.error(f"Error al guardar: {e}")

# =========================================================
# 2. MOTOR DE GMAIL
# =========================================================
EMAIL_USUARIO = "kiritokayabaki@gmail.com" 
EMAIL_PASSWORD = "wkpn qayc mtqj ucut"

def buscar_correos():
    try:
        imap = imaplib.IMAP4_SSL("imap.gmail.com")
        imap.login(EMAIL_USUARIO, EMAIL_PASSWORD)
        imap.select("INBOX", readonly=True)
        _, mensajes = imap.search(None, 'ALL')
        ids = [i.decode() for i in mensajes[0].split()]
        
        lista = []
        for i in reversed(ids[-5:]):
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
if not error_conexion:
    if "seccion" not in st.session_state: st.session_state.seccion = "Inicio"

    @st.fragment(run_every="30s")
    def sincronizar():
        df_actual = cargar_datos_nube()
        if not df_actual.empty:
            ids_nube = df_actual['id'].astype(str).tolist()
            nuevos = [c for c in buscar_correos() if str(c['id']) not in ids_nube]
            if nuevos:
                df_final = pd.concat([pd.DataFrame(nuevos), df_actual], ignore_index=True)
                guardar_datos_nube(df_final)
                st.rerun()
        st.session_state.datos_app = df_actual

    sincronizar()
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
    st.warning("⚠️ Error en la llave PEM. Por favor, revisa el formato en los Secretos.")
