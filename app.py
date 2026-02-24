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

# PEGA AQUÍ TU LLAVE. No importa si es una sola línea larga o tiene \n
LLAVE_BRUTA = """-----BEGIN PRIVATE KEY-----
MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQCxmiHe70esGUZV
vHiu5lfQfNWalqAMPb1IMU66QG9eRy/TnEbFn68bKX94HYSwG7Y2WRvZcmE/rVr6
dWUUya+y28yRtFKK33XNTpXasE2hJryXJu9oe9oCB2Y6Hx61J0mFLD7wDJFzJc5o
LYAvw7s+TfT7TQk1hj2Q8fK/A7v7BOOerMliskZvDtV7wzaHg+QhPEaa6tup2n4w
16aL/8SOrL+GtHEgSESfG32VfodQuudx7zNi8/e+HGHClrQe33XEtf/cUUDvW75b
Y5hH0Oos+I9UQQT3CXt4QbWgYpMvLxTshG8zgZ6Oc+mFcEjykqSEwLZRRD9MswEj
mjDSVrgNAgMBAAECggEAGwqPTqzbGlKM2YAFVgf/ZeCj+1Ik00hROh070fL+ofmv
yAX65psuI7IZVPYVnmTRxQujSGP4d6QS/qCCP/yHcnGx/5tXmAp3Gsf03CPM5hUK
UO9eM2fsJTPwNjhHyihNsueuO4mGWeRvPYB0DJG+QDnJa7vqg4pJdHjKT5gndowi
YyaND1KjUMZrxIXd/cRexTICLugDUSXeSI7P780pjqThIBjPKxLU+7AOGA+fVn9Z
xuQfJpJRDKMIl0FGaHwghxM0Wl35QDQEVMnqgPnRstas7yEKYivwctremKj/hjl1
TRGw+W0/z1R4b3O4RT4OslQbRY45A84FxIsbA5OWNwKBgQDm12iKroXIikLbBY+e
fXiePwzh1BXnDjzfWw+Z7UUiuYRIh7HPcfoRl8nAunq2uGr0nU1pIVq1DE0pQoEY
K5RYnSRBV0wynV+A2XfjfsT3FSXwGJN/LRf12lvU539sX5Xg9429JjHXKPuLKDB0
V/Ceci2QNrmgZHVb3ad7F+OqKwKBgQDE9VG1X/6AWJXVAbKwbxCVKALl3OCfdEtf
LHe/sKwaJcFgIAsATNQkua+QcYc11wjJdJgxp4cHiPOUv7Zv62C9qS+gvrW23r+Q
nn1P5XUYeQPoSmLeHHhI99FJwWhOFCV/TFRI/f6nsz/hrZikYJGfQUKpTYYD4+1PI
vWOQwSsipwKBgAu3Fuki3ktFKQtwhs9mUr7FOGQlnU7ynAhB2NLZBc8zVxFPQajj
getupqCPVjb7uQHdEdaqCK5zh172rxKI86hjoTlnsshG0Ff7sWfsQRbBDgHXXXTw
1ux1Pn/Zl8/qMfMO3TSiQZlHzSxMx9i/tch0xvcwr88CCiq1XxCSL82tAoGBAKGv
YawraZmjHx0Fj9MW2d4YQojAkgVUSquOrZ9HQYEVjXGD3IQajey4Ik/JYt3n8Oaw
OGBKzqZ43r01xGaMK5aG1Pp4lGPS6B+pLB6BW5ZqcN/jToY1QXRqpWJmD7AeyfNW
UOyfuLcW4zAHZaTT/gUcszZPzLiYWWdpUdr7OJXxAoGBAJNE93RrgdH8I4eJyjtj
83kBROXx6W6KWrqXQnnab2NUbP43vDI+vu7WayIDS9VCNdW0yZwyL5RYRDqDagiG
2LlZ8s9RwXRcxrGFRWzbSgzMidbw3+wksOyrrV0f4tbd6BIK5MHZZHbkL8rjPEmV
U5EQz8kl3+kywoTTSEI150ZA
-----END PRIVATE KEY-----"""

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
