import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import imaplib
import email
from email.header import decode_header

# =========================================================
# 1. TUS CREDENCIALES (PEGA AQUÍ LOS DATOS DE TU JSON)
# =========================================================
# Nota: No borres las r antes de las comillas, ayudan a leer texto plano.
PRIVATE_KEY = r"""-----BEGIN PRIVATE KEY-----
PEGA_AQUI_TODA_TU_LLAVE_TAL_CUAL_ESTA_EN_EL_JSON
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

ID_HOJA = "1fdCf2HsS8KKkuqrJ8DwiDednW8lwnz7-WfvuVJwQnBo"
EMAIL_USUARIO = "kiritokayabaki@gmail.com" 
EMAIL_PASSWORD = "wkpn qayc mtqj ucut"

# =========================================================
# 2. LIMPIADOR DE LLAVE PEM (ELIMINA EL ERROR 95)
# =========================================================
def corregir_llave(llave_sucia):
    # Paso 1: Quitar espacios en blanco al inicio y final
    llave = llave_sucia.strip()
    # Paso 2: Si la llave se pegó con \n literales, los convertimos
    llave = llave.replace("\\n", "\n")
    # Paso 3: Asegurar que el encabezado y pie sean limpios
    if "-----BEGIN PRIVATE KEY-----" not in llave:
        llave = "-----BEGIN PRIVATE KEY-----\n" + llave + "\n-----END PRIVATE KEY-----"
    return llave

# =========================================================
# 3. CONEXIÓN A GOOGLE SHEETS
# =========================================================
def conectar_hoja():
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        info = CREDS_INFO.copy()
        info["private_key"] = corregir_llave(PRIVATE_KEY)
        
        credentials = Credentials.from_service_account_info(info, scopes=scope)
        client = gspread.authorize(credentials)
        return client.open_by_key(ID_HOJA).sheet1
    except Exception as e:
        st.error(f"❌ Error de Autenticación: {e}")
        return None

# =========================================================
# 4. INTERFAZ Y LÓGICA
# =========================================================
st.set_page_config(page_title="Control Maquinaria", layout="wide")
st.title("🚜 Gestión de Reportes")

sheet = conectar_hoja()

if sheet:
    st.sidebar.success("✅ Conectado a Google Sheets")
    
    # Cargar datos
    registros = sheet.get_all_records()
    df = pd.DataFrame(registros)

    # Gmail Sync
    if st.button("🔄 Sincronizar Gmail"):
        try:
            imap = imaplib.IMAP4_SSL("imap.gmail.com")
            imap.login(EMAIL_USUARIO, EMAIL_PASSWORD)
            imap.select("INBOX")
            _, msg_ids = imap.search(None, 'ALL')
            
            ids_actuales = [str(i) for i in df['id'].tolist()] if not df.empty else []
            nuevos_datos = []
            
            for i in reversed(msg_ids[0].split()[-10:]):
                id_str = i.decode()
                if id_str not in ids_actuales:
                    _, data = imap.fetch(i, "(RFC822)")
                    mensaje = email.message_from_bytes(data[0][1])
                    asunto, enc = decode_header(mensaje.get("Subject", "Sin Asunto"))[0]
                    if isinstance(asunto, bytes): asunto = asunto.decode(enc or "utf-8")
                    nuevos_datos.append([id_str, asunto, mensaje.get("From"), ""])
            
            if nuevos_datos:
                sheet.append_rows(nuevos_datos)
                st.success(f"¡{len(nuevos_datos)} reportes nuevos!")
                st.rerun()
            else:
                st.info("No hay correos nuevos.")
            imap.logout()
        except Exception as e:
            st.error(f"Error Gmail: {e}")

    # Mostrar Pendientes
    if not df.empty:
        df['comentario'] = df['comentario'].fillna("").astype(str)
        pendientes = df[df['comentario'] == ""]
        
        st.subheader(f"Reportes Pendientes: {len(pendientes)}")
        for idx, row in pendientes.iterrows():
            with st.expander(f"Reporte: {row['asunto']}"):
                fila_num = idx + 2 # +2 porque Sheets empieza en 1 y la fila 1 es encabezado
                sol = st.text_area("Solución:", key=f"t_{row['id']}")
                if st.button("Guardar ✅", key=f"b_{row['id']}"):
                    sheet.update_cell(fila_num, 4, sol) # Columna 4 es 'comentario'
                    st.rerun()
else:
    st.warning("No se pudo establecer la conexión. Revisa que tu llave no tenga caracteres extraños.")
