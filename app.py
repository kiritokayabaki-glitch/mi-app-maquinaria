import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import imaplib
import email
from email.header import decode_header

# --- CONFIGURACIÓN ---
ID_HOJA = "1fdCf2HsS8KKkuqrJ8DwiDednW8lwnz7-WfvuVJwQnBo"
EMAIL_USUARIO = "kiritokayabaki@gmail.com" 
EMAIL_PASSWORD = "wkpn qayc mtqj ucut"

# --- PEGA TU LLAVE AQUÍ ---
LLAVE_BRUTA = """-----BEGIN PRIVATE KEY-----
PEGA_AQUÍ_TODA_TU_LLAVE_TAL_CUAL
-----END PRIVATE KEY-----"""

CREDS_INFO = {
  "type": "service_account",
  "project_id": "notificaciones-82eaf",
  "private_key_id": "453af9d7c00be01c7650168a473a0e5181372646",
  "client_email": "mi-app-maquinaria@notificaciones-82eaf.iam.gserviceaccount.com",
  "client_id": "110397704418799334660",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/mi-app-maquinaria%40notificaciones-82eaf.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}

def limpiar_llave(llave):
    # Esta línea elimina el carácter 195 y otros invisibles
    llave_limpia = llave.encode("ascii", "ignore").decode("ascii")
    # Arregla los saltos de línea si se pegaron mal
    return llave_limpia.replace("\\n", "\n").strip()

@st.cache_resource
def conectar_google():
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        info = CREDS_INFO.copy()
        info["private_key"] = limpiar_llave(LLAVE_BRUTA)
        
        creds = Credentials.from_service_account_info(info, scopes=scope)
        return gspread.authorize(creds).open_by_key(ID_HOJA).sheet1
    except Exception as e:
        st.error(f"❌ Error de Autenticación: {e}")
        return None

# --- INTERFAZ ---
st.set_page_config(page_title="Control Maquinaria", layout="wide")
st.title("🚜 Control de Mantenimiento")

hoja = conectar_google()

if hoja:
    st.success("✅ ¡Conectado con éxito!")
    # Aquí iría el resto de tu lógica de carga de datos y Gmail...
else:
    st.warning("La llave sigue teniendo problemas. Por favor, revisa el paso de 'Generar Llave Nueva'.")
