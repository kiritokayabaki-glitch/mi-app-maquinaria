import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import imaplib
import email
from email.header import decode_header

# --- 1. TUS CREDENCIALES (RELLENA CON TU JSON NUEVO) ---
ID_HOJA = "1fdCf2HsS8KKkuqrJ8DwiDednW8lwnz7-WfvuVJwQnBo"
EMAIL_USUARIO = "kiritokayabaki@gmail.com" 
EMAIL_PASSWORD = "wkpn qayc mtqj ucut"

CREDS_INFO = {
  "type": "service_account",
  "project_id": "notificaciones-82eaf",
  "private_key_id": "f698b836b566c626ce08d06cf5d6062909a1341f", # <--- REVISA ESTE ID EN TU JSON
  "private_key": """-----BEGIN PRIVATE KEY-----
PEGA_AQUI_TODA_TU_LLAVE_COMPLETA_CON_SUS_SALTOS_DE_LINEA
-----END PRIVATE KEY-----""",
  "client_email": "mi-app-maquinaria@notificaciones-82eaf.iam.gserviceaccount.com",
  "client_id": "110397704418799334660",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/mi-app-maquinaria%40notificaciones-82eaf.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}

# --- 2. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Gestión Maquinaria", layout="wide")
st.title("🚜 Panel de Control de Mantenimiento")

# --- 3. FUNCIÓN DE CONEXIÓN ---
@st.cache_resource
def conectar_google():
    try:
        info = CREDS_INFO.copy()
        # Esto soluciona el error de "Invalid JWT Signature"
        info["private_key"] = info["private_key"].replace("\\n", "\n")
        
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(info, scopes=scope)
        client = gspread.authorize(creds)
        return client.open_by_key(ID_HOJA).sheet1
    except Exception as e:
        st.error(f"❌ Error de Conexión: {e}")
        return None

# --- 4. FUNCIÓN DE GMAIL ---
def buscar_correos_nuevos(ids_existentes):
    try:
        imap = imaplib.IMAP4_SSL("imap.gmail.com")
        imap.login(EMAIL_USUARIO, EMAIL_PASSWORD)
        imap.select("INBOX")
        _, data = imap.search(None, 'ALL')
        mail_ids = data[0].split()
        
        nuevos = []
        # Revisamos los últimos 10 correos
        for m_id in reversed(mail_ids[-10:]):
            id_str = m_id.decode()
            if id_str not in ids_existentes:
                _, m_data = imap.fetch(m_id, "(RFC822)")
                msg = email.message_from_bytes(m_data[0][1])
                asunto, enc = decode_header(msg.get("Subject", "Sin Asunto"))[0]
                if isinstance(asunto, bytes): asunto = asunto.decode(enc or "utf-8")
                # Estructura: id, asunto, remitente, comentario_vacio
                nuevos.append([id_str, asunto, msg.get("From"), ""])
        
        imap.logout()
        return nuevos
    except Exception as e:
        st.error(f"Error Gmail: {e}")
        return []

# --- 5. LÓGICA PRINCIPAL ---
hoja = conectar_google()

if hoja:
    st.sidebar.success("✅ Conectado a la nube")
    
    # Leer datos actuales
    try:
        registros = hoja.get_all_records()
        df = pd.DataFrame(registros)
    except:
        df = pd.DataFrame(columns=["id", "asunto", "de", "comentario"])

    # Botón Sincronizar
    if st.button("🔄 Sincronizar con Gmail"):
        with st.spinner("Buscando nuevos correos..."):
            ids_actuales = df['id'].astype(str).tolist() if not df.empty else []
            nuevos = buscar_correos_nuevos(ids_actuales)
            
            if nuevos:
                hoja.append_rows(nuevos)
                st.success(f"¡Se agregaron {len(nuevos)} reportes nuevos!")
                st.rerun()
            else:
                st.info("No hay correos nuevos.")

    # Mostrar Reportes Pendientes
    st.subheader("📋 Reportes de Falla")
    if not df.empty:
        # Asegurar que la columna comentario no tenga nulos
        df['comentario'] = df['comentario'].fillna("").astype(str)
        pendientes = df[df['comentario'] == ""]
        
        if pendientes.empty:
            st.write("✨ No hay reportes pendientes de solución.")
        
        for idx, row in pendientes.iterrows():
            with st.expander(f"🛠️ {row['asunto']} (Remitente: {row['de']})"):
                solucion = st.text_area("Describa la reparación realizada:", key=f"sol_{row['id']}")
                if st.button("Marcar como Reparado ✅", key=f"btn_{row['id']}"):
                    # En Google Sheets, la fila es índice + 2
                    hoja.update_cell(idx + 2, 4, solucion)
                    st.success("Reporte guardado con éxito.")
                    st.rerun()
    else:
        st.write("La base de datos está vacía. Presiona Sincronizar.")
else:
    st.warning("El sistema no puede arrancar sin conexión a Google Sheets.")
