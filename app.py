import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import imaplib
import email
from email.header import decode_header
import json

# --- CONFIGURACIÓN ---
ID_HOJA = "1fdCf2HsS8KKkuqrJ8DwiDednW8lwnz7-WfvuVJwQnBo"
EMAIL_USUARIO = "kiritokayabaki@gmail.com" 
EMAIL_PASSWORD = "wkpn qayc mtqj ucut"

# --- PEGA TU JSON COMPLETO AQUÍ ---
# Abre tu archivo .json descargado, copia TODO el contenido y pégalo entre las comillas
JSON_DATA = {
  "type": "service_account",
  "project_id": "notificaciones-82eaf",
  "private_key_id": "f698b836b566c626ce08d06cf5d6062909a1341f",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQCxmiHe70esGUZV\nvHiu5lfQfNWalqAMPb1IMU66QG9eRy/TnEbFn68bKX94HYSwG7Y2WRvZcmE/rVr6\ndWUUya+y28yRtFKK33XNTpXasE2hJryXJu9oe9oCB2Y6Hx61J0mFLD7wDJFzJc5o\nLYAvw7s+TfT7TQk1hj2Q8fK/A7v7BOOerMliskZvDtV7wzaHg+QhPEaa6tup2n4w\n16aL/8SOrL+GtHEgSESfG32VfodQuudx7zNi8/e+HGHClrQe33XEtf/cUUDvW75b\nY5hH0Oos+I9UQQT3CXt4QbWgYpMvLxTshG8zgZ6Oc+mFcEjykqSEwLZRRD9MswEj\nmjDSVrgNAgMBAAECggEAGwqPTqzbGlKM2YAFVgf/ZeCj+1Ik00hROh070fL+ofmv\nyAX65psuI7IZVPYVnmTRxQujSGP4d6QS/qCCP/yHcnGx/5tXmAp3Gsf03CPM5hUK\nUO9eM2fsJTPwNjhHyihNsueuO4mGWeRvPYB0DJG+QDnJa7vqg4pJdHjKT5gndowi\nYyaND1KjUMZrxIXd/cRexTICLugDUSXeSI7P780pjqThIBjPKxLU+7AOGA+fVn9Z\nxuQfJpJRDKMIl0FGaHwghxM0Wl35QDQEVMnqgPnRstas7yEKYivwctremKj/hjl1\nTRGw+W0/z1R4b3O4RT4OslQbRY45A84FxIsbA5OWNwKBgQDm12iKroXIikLbBY+e\nfXiePwzh1BXnDjzfWw+Z7UUiuYRIh7HPcfoRl8nAunq2uGr0nU1pIVq1DE0pQoEY\nK5RYnSRBV0wynV+A2XfjfsT3FSXwGJN/LRf12lvU539sX5Xg9429JjHXKPuLKDB0\nV/Ceci2QNrmgZHVb3ad7F+OqKwKBgQDE9VG1X/6AWJXVAbKwbxCVKALl3OCfdEtf\nLHe/sKwaJcFgIAsATNQkua+QcYc11wjJdJgxp4cHiPOUv7Zv62C9qS+gvrW23r+Q\nn1P5XUYeQPoSmLeHHhI99FJwWhOFCV/TFRI/f6nsz/hrZikYJGfQUKpTYYD4+1PI\nvWOQwSsipwKBgAu3Fuki3ktFKQtwhs9mUr7FOGQlnU7ynAhB2NLZBc8zVxFPQajj\ngetupqCPVjb7uQHdEdaqCK5zh172rxKI86hjoTlnsshG0Ff7sWfsQRbBDgHXXXTw\n1ux1Pn/Zl8/qMfMO3TSiQZlHzSxMx9i/tch0xvcwr88CCiq1XxCSL82tAoGBAKGv\nYawraZmjHx0Fj9MW2d4YQojAkgVUSquOrZ9HQYEVjXGD3IQajey4Ik/JYt3n8Oaw\nOGBKzqZ43r01xGaMK5aG1Pp4lGPS6B+pLB6BW5ZqcN/jToY1QXRqpWJmD7AeyfNW\nUOyfuLcW4zAHZaTT/gUcszZPzLiYWWdpUdr7OJXxAoGBAJNE93RrgdH8I4eJyjtj\n83kBROXx6W6KWrqXQnnab2NUbP43vDI+vu7WayIDS9VCNdW0yZwyL5RYRDqDagiG\n2LlZ8s9RwXRcxrGFRWzbSgzMidbw3+wksOyrrV0f4tbd6BIK5MHZZHbkL8rjPEmV\nU5EQz8kl3+kywoTTSEI150ZA\n-----END PRIVATE KEY-----\n",
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
        # Copiamos para no alterar el original
        info = JSON_DATA.copy()
        # Reparamos los saltos de línea \n que se vuelven texto
        info["private_key"] = info["private_key"].replace("\\n", "\n")
        
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(info, scopes=scope)
        client = gspread.authorize(creds)
        return client.open_by_key(ID_HOJA).sheet1
    except Exception as e:
        st.error(f"❌ Error de Conexión: {e}")
        return None

# --- LÓGICA PRINCIPAL ---
st.title("🚜 Panel de Control")
hoja = conectar()

if hoja:
    st.success("✅ ¡CONECTADO EXITOSAMENTE!")
    # Leer datos
    try:
        data = hoja.get_all_records()
        df = pd.DataFrame(data)
        
        if st.button("🔄 Sincronizar"):
            # Aquí iría tu función de Gmail (la que ya tienes)
            st.info("Buscando correos...")
            
        if not df.empty:
            st.dataframe(df)
        else:
            st.write("Conectado, pero la hoja no tiene datos.")
            
    except Exception as e:
        st.error(f"Error al leer datos: {e}")
