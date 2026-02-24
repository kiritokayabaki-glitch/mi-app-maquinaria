import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import imaplib
import email
from email.header import decode_header
import re

# ==========================================
# 1. CONFIGURACIÓN Y CREDENCIALES
# ==========================================
ID_HOJA = "1fdCf2HsS8KKkuqrJ8DwiDednW8lwnz7-WfvuVJwQnBo"
EMAIL_USUARIO = "kiritokayabaki@gmail.com" 
EMAIL_PASSWORD = "wkpn qayc mtqj ucut"

# PEGA AQUÍ TODO EL CONTENIDO DE "private_key" QUE VIENE EN EL JSON
LLAVE_DE_GOOGLE = """TU_LLAVE_AQUI"""

CREDS_INFO = {
  "type": "service_account",
  "project_id": "notificaciones-82eaf",
  "private_key_id": "f698b836b566c626ce08d06cf5d6062909a1341f",
  "client_email": "mi-app-maquinaria@notificaciones-82eaf.iam.gserviceaccount.com",
  "client_id": "110397704418799334660",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/mi-app-maquinaria%40notificaciones-82eaf.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}

# ==========================================
# 2. PURIFICADOR DE LLAVE (ANTI-ERROR 95)
# ==========================================
def purificar_llave(texto):
    # Paso A: Convertir \n de texto en saltos de línea reales
    llave = texto.replace("\\n", "\n")
    # Paso B: Limpiar espacios y caracteres raros en los extremos
    llave = llave.strip()
    # Paso C: Forzar que los guiones sean estándar (Esto mata el Error 95)
    # Reemplazamos cualquier guion largo o guion bajo por guion normal
    llave = llave.replace("_", "-").replace("—", "-")
    
    # Asegurar que tenga el formato PEM correcto
    if "-----BEGIN PRIVATE KEY-----" not in llave:
        llave = "-----BEGIN PRIVATE KEY-----\n" + llave
    if "-----END PRIVATE KEY-----" not in llave:
        llave = llave + "\n-----END PRIVATE KEY-----"
    
    return llave

# ==========================================
# 3. CONEXIÓN A GOOGLE SHEETS
# ==========================================
@st.cache_resource
def conectar_hoja():
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        info = CREDS_INFO.copy()
        info["private_key"] = purificar_llave(LLAVE_DE_GOOGLE)
        
        credentials = Credentials.from_service_account_info(info, scopes=scope)
        client = gspread.authorize(credentials)
        return client.open_by_key(ID_HOJA).sheet1
    except Exception as e:
        st.error(f"❌ Error de Autenticación: {e}")
        return None

# ==========================================
# 4. FUNCIÓN GMAIL
# ==========================================
def sync_gmail(ids_viejos):
    try:
        imap = imaplib.IMAP4_SSL("imap.gmail.com")
        imap.login(EMAIL_USUARIO, EMAIL_PASSWORD)
        imap.select("INBOX")
        _, data = imap.search(None, 'ALL')
        mail_ids = data[0].split()
        nuevos = []
        for m_id in reversed(mail_ids[-10:]): # Solo últimos 10 para rapidez
            id_s = m_id.decode()
            if id_s not in ids_viejos:
                _, m_data = imap.fetch(m_id, "(RFC822)")
                msg = email.message_from_bytes(m_data[0][1])
                asunto, enc = decode_header(msg.get("Subject", "Sin Asunto"))[0]
                if isinstance(asunto, bytes): asunto = asunto.decode(enc or "utf-8")
                nuevos.append([id_s, asunto, msg.get("From"), ""])
        imap.logout()
        return nuevos
    except: return []

# ==========================================
# 5. INTERFAZ DE USUARIO (STREAMLIT)
# ==========================================
st.set_page_config(page_title="Control Maquinaria", layout="wide")
st.title("🚜 Sistema de Reportes de Maquinaria")

hoja = conectar_hoja()

if hoja:
    st.sidebar.success("✅ Conectado a Google Sheets")
    
    # Cargar Datos
    try:
        raw_data = hoja.get_all_records()
        df = pd.DataFrame(raw_data)
    except:
        df = pd.DataFrame(columns=["id", "asunto", "de", "comentario"])

    # Botón Sincronizar
    if st.button("🔄 Sincronizar con Gmail"):
        ids_viejos = df['id'].astype(str).tolist() if not df.empty else []
        nuevos = sync_gmail(ids_viejos)
        if nuevos:
            hoja.append_rows(nuevos)
            st.success(f"¡{len(nuevos)} nuevos reportes!")
            st.rerun()
        else:
            st.info("No hay correos nuevos.")

    # Mostrar Pendientes
    if not df.empty:
        df['comentario'] = df['comentario'].fillna("").astype(str)
        pendientes = df[df['comentario'] == ""]
        
        st.subheader(f"Pendientes: {len(pendientes)}")
        for idx, row in pendientes.iterrows():
            with st.expander(f"Reporte: {row['asunto']}"):
                st.write(f"**De:** {row['de']}")
                resp = st.text_area("Solución:", key=f"r_{row['id']}")
                if st.button("Guardar solución ✅", key=f"b_{row['id']}"):
                    # Fila: idx + 2 (1 por encabezado, 1 por base 1 de Sheets)
                    hoja.update_cell(idx + 2, 4, resp)
                    st.success("Guardado.")
                    st.rerun()
    else:
        st.write("La hoja está vacía. Usa el botón de sincronizar.")
