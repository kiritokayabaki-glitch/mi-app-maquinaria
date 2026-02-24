import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import imaplib
import email
from email.header import decode_header

# =========================================================
# 1. CREDENCIALES DIRECTAS (REEMPLAZA CON TU JSON)
# =========================================================
CREDS = {
  "type": "service_account",
  "project_id": "notificaciones-82eaf",
  "private_key_id": "453af9d7c00be01c7650168a473a0e5181372646",
  "private_key": """-----BEGIN PRIVATE KEY-----
PEGA_AQUI_TODA_TU_LLAVE_TAL_CUAL_ESTA_EN_EL_JSON
-----END PRIVATE KEY-----""",
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
# 2. FUNCIONES DE CONEXIÓN
# =========================================================

def conectar_hoja():
    try:
        # Definimos los permisos necesarios
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        # Limpiamos la llave por si tiene caracteres invisibles
        creds_dict = CREDS.copy()
        creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
        
        credentials = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(credentials)
        return client.open_by_key(ID_HOJA).sheet1
    except Exception as e:
        st.error(f"❌ Error de Autenticación: {e}")
        return None

# =========================================================
# 3. MOTOR DE GMAIL
# =========================================================

def buscar_correos_nuevos(ids_existentes):
    try:
        imap = imaplib.IMAP4_SSL("imap.gmail.com")
        imap.login(EMAIL_USUARIO, EMAIL_PASSWORD)
        imap.select("INBOX", readonly=True)
        _, mensajes = imap.search(None, 'ALL')
        ids = mensajes[0].split()
        
        nuevos = []
        for i in reversed(ids[-10:]): # Revisar los últimos 10
            idx_str = i.decode()
            if idx_str not in ids_existentes:
                res, msg = imap.fetch(i, "(RFC822)")
                for respuesta in msg:
                    if isinstance(respuesta, tuple):
                        mensaje = email.message_from_bytes(respuesta[1])
                        asunto, enc = decode_header(mensaje.get("Subject", "Sin Asunto"))[0]
                        if isinstance(asunto, bytes): asunto = asunto.decode(enc or "utf-8")
                        nuevos.append([idx_str, asunto, mensaje.get("From"), ""])
        imap.logout()
        return nuevos
    except Exception as e:
        st.warning(f"Aviso Gmail: {e}")
        return []

# =========================================================
# 4. INTERFAZ Y LÓGICA
# =========================================================

st.set_page_config(page_title="Control Maquinaria", layout="wide")
st.title("🚜 Gestión de Reportes (Vía Directa)")

sheet = conectar_hoja()

if sheet:
    # Leer datos actuales
    data = sheet.get_all_values()
    if not data: # Si la hoja está totalmente vacía, crear encabezados
        sheet.append_row(["id", "asunto", "de", "comentario"])
        data = [["id", "asunto", "de", "comentario"]]
    
    df = pd.DataFrame(data[1:], columns=data[0])
    
    # Sincronización
    if st.button("🔄 Sincronizar Gmail"):
        ids_actuales = df['id'].tolist() if not df.empty else []
        nuevos_filas = buscar_correos_nuevos(ids_actuales)
        if nuevos_filas:
            sheet.append_rows(nuevos_filas)
            st.success(f"Se agregaron {len(nuevos_filas)} reportes.")
            st.rerun()
        else:
            st.info("No hay reportes nuevos.")

    # Mostrar Pendientes
    if not df.empty:
        # Asegurar que la columna comentario exista
        if 'comentario' not in df.columns: df['comentario'] = ""
        
        pendientes = df[df['comentario'] == ""]
        st.subheader(f"Reportes Pendientes: {len(pendientes)}")
        
        for idx, row in pendientes.iterrows():
            with st.expander(f"Reporte: {row['asunto']}"):
                st.write(f"**De:** {row['de']}")
                # El índice en Google Sheets empieza en 2 (1 es encabezado)
                fila_excel = idx + 2 
                nota = st.text_area("Solución:", key=f"t_{row['id']}")
                if st.button("Guardar ✅", key=f"b_{row['id']}"):
                    # Actualizar celda de comentario (Columna D es la 4)
                    sheet.update_cell(fila_excel, 4, nota)
                    st.rerun()
    else:
        st.write("La hoja está lista para recibir datos.")
