import streamlit as st
import pandas as pd
import imaplib
import email
from email.header import decode_header
import gspread
from google.oauth2.service_account import Credentials

# =========================================================
# 1. CONFIGURACIÓN MANUAL (SIN SECRETS PARA LA LLAVE)
# =========================================================

# REEMPLAZA LOS DATOS DE ABAJO CON LOS DE TU ARCHIVO JSON
GOOGLE_CREDENTIALS = {
  "type": "service_account",
  "project_id": "notificaciones-82eaf",
  "private_key_id": "453af9d7c00be01c7650168a473a0e5181372646",
  "private_key": "-----BEGIN PRIVATE KEY-----\nTU_LLAVE_AQUI\n-----END PRIVATE KEY-----\n",
  "client_email": "mi-app-maquinaria@notificaciones-82eaf.iam.gserviceaccount.com",
  "client_id": "110397704418799334660",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/mi-app-maquinaria%40notificaciones-82eaf.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}

ID_HOJA = "1fdCf2HsS8KKkuqrJ8DwiDednW8lwnz7-WfvuVJwQnBo"
EMAIL_USUARIO = "kiritokayabaki@gmail.com" 
EMAIL_PASSWORD = "wkpn qayc mtqj ucut"

# Conexión Robusta
def conectar_google():
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(GOOGLE_CREDENTIALS, scopes=scope)
        client = gspread.authorize(creds)
        return client.open_by_key(ID_HOJA).sheet1
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return None

hoja = conectar_google()

# =========================================================
# 2. FUNCIONES DE DATOS
# =========================================================

def cargar_datos():
    if hoja:
        data = hoja.get_all_records()
        return pd.DataFrame(data)
    return pd.DataFrame()

def guardar_datos(df):
    if hoja:
        hoja.clear()
        # Actualizar con encabezados y datos
        hoja.update([df.columns.values.tolist()] + df.values.tolist())
        st.success("✅ ¡Base de datos actualizada!")

# =========================================================
# 3. MOTOR DE GMAIL
# =========================================================

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
# 4. INTERFAZ STREAMLIT
# =========================================================
st.set_page_config(page_title="Maquinaria Dash", layout="wide")
st.title("🚜 Gestión de Reportes")

if "seccion" not in st.session_state: st.session_state.seccion = "Inicio"

if hoja:
    df = cargar_datos()
    
    # Lógica de sincronización automática
    ids_en_nube = df['id'].astype(str).tolist() if not df.empty else []
    correos_nuevos = [c for c in buscar_correos() if str(c['id']) not in ids_en_nube]
    
    if correos_nuevos:
        df_nuevos = pd.DataFrame(correos_nuevos)
        df = pd.concat([df_nuevos, df], ignore_index=True)
        guardar_datos(df)
        st.rerun()

    # Interfaz de usuario
    df['comentario'] = df['comentario'].fillna("")
    pendientes = df[df['comentario'] == ""]
    
    st.sidebar.title("Menú")
    if st.sidebar.button("🏠 Inicio"): st.session_state.seccion = "Inicio"
    if st.sidebar.button(f"🔴 Pendientes ({len(pendientes)})"): st.session_state.seccion = "Pendientes"

    if st.session_state.seccion == "Inicio":
        st.metric("Total Reportes", len(df))
        st.metric("Pendientes", len(pendientes))
        st.dataframe(df)

    elif st.session_state.seccion == "Pendientes":
        for idx, row in pendientes.iterrows():
            with st.expander(f"Reporte: {row['asunto']}"):
                comentario = st.text_area("Solución:", key=f"t_{row['id']}")
                if st.button("Guardar ✅", key=f"b_{row['id']}"):
                    df.loc[df['id'] == row['id'], 'comentario'] = comentario
                    guardar_datos(df)
                    st.rerun()
