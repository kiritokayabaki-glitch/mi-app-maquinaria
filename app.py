import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import imaplib
import email
from email.header import decode_header

# --- CONFIGURACIÓN DE IDENTIDAD ---
ID_HOJA = "1fdCf2HsS8KKkuqrJ8DwiDednW8lwnz7-WfvuVJwQnBo"
EMAIL_USUARIO = "kiritokayabaki@gmail.com" 
EMAIL_PASSWORD = "wkpn qayc mtqj ucut"

# --- CREDENCIALES (PÉGALAS AQUÍ) ---
# Usa las triples comillas para que los saltos de línea se respeten solos
CREDS_DICT = {
  "type": "service_account",
  "project_id": "notificaciones-82eaf",
  "private_key_id": "453af9d7c00be01c7650168a473a0e5181372646",
  "private_key": """-----BEGIN PRIVATE KEY-----
AQUÍ_PEGA_TU_LLAVE_COMPLETA_SIN_EDITAR_NADA
-----END PRIVATE KEY-----""",
  "client_email": "mi-app-maquinaria@notificaciones-82eaf.iam.gserviceaccount.com",
  "client_id": "110397704418799334660",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/mi-app-maquinaria%40notificaciones-82eaf.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}

st.set_page_config(page_title="Gestión Maquinaria", layout="wide")

@st.cache_resource
def conectar():
    try:
        # Aquí forzamos la corrección de los saltos de línea por si acaso
        info = CREDS_DICT.copy()
        info["private_key"] = info["private_key"].replace("\\n", "\n")
        
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(info, scopes=scope)
        return gspread.authorize(creds).open_by_key(ID_HOJA).sheet1
    except Exception as e:
        st.error(f"❌ Error de Autenticación: {e}")
        return None

hoja = conectar()

# --- INTERFAZ ---
st.title("🚜 Control de Mantenimiento")

if hoja:
    st.sidebar.success("✅ Conectado")
    
    # Obtener datos de la hoja
    try:
        data = hoja.get_all_records()
        df = pd.DataFrame(data)
    except:
        df = pd.DataFrame()

    # Sincronizar Gmail
    if st.button("🔄 Sincronizar Gmail"):
        try:
            imap = imaplib.IMAP4_SSL("imap.gmail.com")
            imap.login(EMAIL_USUARIO, EMAIL_PASSWORD)
            imap.select("INBOX")
            _, msg_ids = imap.search(None, 'ALL')
            
            existentes = df['id'].astype(str).tolist() if not df.empty else []
            nuevos = []
            
            for m_id in reversed(msg_ids[0].split()[-10:]):
                id_s = m_id.decode()
                if id_s not in existentes:
                    _, m_data = imap.fetch(m_id, "(RFC822)")
                    msg = email.message_from_bytes(m_data[0][1])
                    asunto, enc = decode_header(msg.get("Subject", "Sin Asunto"))[0]
                    if isinstance(asunto, bytes): asunto = asunto.decode(enc or "utf-8")
                    nuevos.append([id_s, asunto, msg.get("From"), ""])
            
            if nuevos:
                hoja.append_rows(nuevos)
                st.rerun()
            imap.logout()
        except Exception as e:
            st.error(f"Error Gmail: {e}")

    # Mostrar para editar
    if not df.empty:
        df['comentario'] = df['comentario'].fillna("").astype(str)
        pendientes = df[df['comentario'] == ""]
        
        for idx, row in pendientes.iterrows():
            with st.expander(f"Reporte: {row['asunto']}"):
                sol = st.text_area("Solución:", key=f"s_{row['id']}")
                if st.button("Guardar ✅", key=f"b_{row['id']}"):
                    # +2 porque Sheets empieza en 1 y la fila 1 es encabezado
                    hoja.update_cell(idx + 2, 4, sol)
                    st.rerun()
else:
    st.warning("No se pudo conectar. Si el error 'short data' persiste, la llave del JSON está incompleta.")
