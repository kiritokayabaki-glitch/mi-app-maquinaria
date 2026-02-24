import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import imaplib
import email
from email.header import decode_header

# ==========================================
# 1. CONFIGURACIÓN
# ==========================================
ID_HOJA = "1fdCf2HsS8KKkuqrJ8DwiDednW8lwnz7-WfvuVJwQnBo"
EMAIL_USUARIO = "kiritokayabaki@gmail.com" 
EMAIL_PASSWORD = "wkpn qayc mtqj ucut"


# --- NO TOCAR ESTE DICCIONARIO ---
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
# 2. PROCESO DE AUTENTICACIÓN
# ==========================================
st.set_page_config(page_title="Gestión Maquinaria", layout="wide")
st.title("🚜 Control de Mantenimiento")

@st.cache_resource
def obtener_cliente():
    try:
        # Limpieza definitiva de la llave
        key = LLAVE_BRUTA.strip()
        # Si la llave tiene los \n como texto, los convertimos a saltos reales
        if "\\n" in key:
            key = key.replace("\\n", "\n")
            
        info = CREDS_INFO.copy()
        info["private_key"] = key
        
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(info, scopes=scope)
        return gspread.authorize(creds).open_by_key(ID_HOJA).sheet1
    except Exception as e:
        st.error(f"❌ Error Crítico: {e}")
        return None

hoja = obtener_cliente()

# ==========================================
# 3. LÓGICA DE LA APP
# ==========================================
if hoja:
    st.sidebar.success("✅ Conectado a la Base de Datos")
    
    try:
        data = hoja.get_all_records()
        df = pd.DataFrame(data)
    except:
        df = pd.DataFrame(columns=["id", "asunto", "de", "comentario"])

    # Botón Sincronizar Gmail
    if st.button("🔄 Sincronizar Reportes"):
        try:
            imap = imaplib.IMAP4_SSL("imap.gmail.com")
            imap.login(EMAIL_USUARIO, EMAIL_PASSWORD)
            imap.select("INBOX")
            _, response = imap.search(None, 'ALL')
            
            ids_existentes = df['id'].astype(str).tolist() if not df.empty else []
            nuevos = []
            
            for m_id in reversed(response[0].split()[-10:]):
                if m_id.decode() not in ids_existentes:
                    _, m_data = imap.fetch(m_id, "(RFC822)")
                    msg = email.message_from_bytes(m_data[0][1])
                    asunto, enc = decode_header(msg.get("Subject", "Sin Asunto"))[0]
                    if isinstance(asunto, bytes): asunto = asunto.decode(enc or "utf-8")
                    nuevos.append([m_id.decode(), asunto, msg.get("From"), ""])
            
            if nuevos:
                hoja.append_rows(nuevos)
                st.success(f"¡{len(nuevos)} reportes nuevos!")
                st.rerun()
            imap.logout()
        except Exception as e:
            st.error(f"Error de Gmail: {e}")

    # Mostrar pendientes
    if not df.empty:
        df['comentario'] = df['comentario'].fillna("").astype(str)
        pendientes = df[df['comentario'] == ""]
        
        for idx, row in pendientes.iterrows():
            with st.expander(f"Reporte: {row['asunto']}"):
                sol = st.text_area("Solución:", key=f"s_{row['id']}")
                if st.button("Guardar ✅", key=f"b_{row['id']}"):
                    hoja.update_cell(idx + 2, 4, sol)
                    st.rerun()
    else:
        st.info("Presiona sincronizar para cargar datos.")
