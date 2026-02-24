import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import imaplib
import email
from email.header import decode_header
import re

# =========================================================
# 1. TUS DATOS (RELLENA CON TU JSON)
# =========================================================
ID_HOJA = "1fdCf2HsS8KKkuqrJ8DwiDednW8lwnz7-WfvuVJwQnBo"
EMAIL_USUARIO = "kiritokayabaki@gmail.com" 
EMAIL_PASSWORD = "wkpn qayc mtqj ucut"

# PEGA AQUÍ SOLO EL TEXTO LARGO DE LA LLAVE (LO QUE ESTÁ ENTRE COMILLAS EN EL JSON)
# No incluyas los \n, solo pega el bloque de texto si puedes.
LLAVE_BRUTA = """
-----BEGIN PRIVATE KEY-----
PEGA_AQUI_EL_CONTENIDO_DE_TU_LLAVE
-----END PRIVATE KEY-----
"""

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

# =========================================================
# 2. LIMPIADOR AGRESIVO DE LLAVE (EVITA EL ERROR 4, 95)
# =========================================================
def limpiar_llave_maestra(raw_key):
    # Eliminamos el texto de cabecera y pie para limpiar el centro
    cuerpo = raw_key.replace("-----BEGIN PRIVATE KEY-----", "")
    cuerpo = cuerpo.replace("-----END PRIVATE KEY-----", "")
    # Quitamos espacios, saltos de línea y caracteres extraños (como el error 95)
    cuerpo = re.sub(r'\s+', '', cuerpo)
    # Reconstruimos la llave con el formato exacto que pide el estándar PEM
    llave_final = "-----BEGIN PRIVATE KEY-----\n" + cuerpo + "\n-----END PRIVATE KEY-----\n"
    return llave_final

# =========================================================
# 3. CONEXIÓN Y LÓGICA
# =========================================================
st.set_page_config(page_title="Gestión Maquinaria", layout="wide")
st.title("🚜 Control de Maquinaria")

@st.cache_resource
def obtener_cliente_google():
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        info = CREDS_INFO.copy()
        info["private_key"] = limpiar_llave_maestra(LLAVE_BRUTA)
        
        creds = Credentials.from_service_account_info(info, scopes=scope)
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"❌ Error de Autenticación: {e}")
        return None

cliente = obtener_cliente_google()

if cliente:
    try:
        hoja = cliente.open_by_key(ID_HOJA).sheet1
        st.sidebar.success("✅ Conectado a Google Sheets")
        
        # Cargar Datos
        records = hoja.get_all_records()
        df = pd.DataFrame(records)

        # Sincronización Gmail
        if st.button("🔄 Sincronizar con Gmail"):
            with st.spinner("Buscando correos..."):
                imap = imaplib.IMAP4_SSL("imap.gmail.com")
                imap.login(EMAIL_USUARIO, EMAIL_PASSWORD)
                imap.select("INBOX")
                _, data = imap.search(None, 'ALL')
                mail_ids = data[0].split()
                
                existentes = df['id'].astype(str).tolist() if not df.empty else []
                nuevos = []
                
                for m_id in reversed(mail_ids[-10:]):
                    id_s = m_id.decode()
                    if id_s not in existentes:
                        _, m_data = imap.fetch(m_id, "(RFC822)")
                        msg = email.message_from_bytes(m_data[0][1])
                        asunto, enc = decode_header(msg.get("Subject", "Sin Asunto"))[0]
                        if isinstance(asunto, bytes): asunto = asunto.decode(enc or "utf-8")
                        nuevos.append([id_s, asunto, msg.get("From"), ""])
                
                if nuevos:
                    hoja.append_rows(nuevos)
                    st.success(f"¡{len(nuevos)} nuevos reportes!")
                    st.rerun()
                else:
                    st.info("No hay correos nuevos.")
                imap.logout()

        # Mostrar Tabla de Trabajo
        if not df.empty:
            df['comentario'] = df['comentario'].fillna("").astype(str)
            pendientes = df[df['comentario'] == ""]
            
            st.subheader(f"Pendientes: {len(pendientes)}")
            for idx, row in pendientes.iterrows():
                with st.expander(f"Asunto: {row['asunto']}"):
                    solucion = st.text_area("Solución:", key=f"sol_{row['id']}")
                    if st.button("Guardar ✅", key=f"btn_{row['id']}"):
                        # +2 porque gspread usa base 1 y hay encabezado
                        hoja.update_cell(idx + 2, 4, solucion)
                        st.rerun()
        else:
            st.info("La hoja está vacía. Haz clic en sincronizar.")

    except Exception as e:
        st.error(f"Error de lectura: {e}")
