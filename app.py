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

# PEGA AQUÍ EL CONTENIDO DE TU LLAVE (Solo la parte larga de letras y números)
LLAVE_BRUTA = """
PEGA_AQUI_TODO_EL_TEXTO_DE_TU_LLAVE
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
# 2. RECONSTRUCTOR DE LLAVE (ELIMINA EL ERROR 4, 95)
# =========================================================
def reconstruir_llave_pem(texto_sucio):
    # Paso 1: Quitar encabezados y pies si existen
    cuerpo = texto_sucio.replace("-----BEGIN PRIVATE KEY-----", "")
    cuerpo = cuerpo.replace("-----END PRIVATE KEY-----", "")
    cuerpo = cuerpo.replace("\\n", "")
    
    # Paso 2: Quitar CUALQUIER cosa que no sea base64 (letras, números, +, /, =)
    # Esto borra los guiones bajos invisibles que causan tu error
    cuerpo_limpio = re.sub(r'[^A-Za-z0-9+/=]', '', cuerpo)
    
    # Paso 3: Reconstruir con guiones nuevos y limpios generados por el código
    header = "-----BEGIN PRIVATE KEY-----"
    footer = "-----END PRIVATE KEY-----"
    
    # Google espera bloques de 64 caracteres
    lineas = [cuerpo_limpio[i:i+64] for i in range(0, len(cuerpo_limpio), 64)]
    return f"{header}\n" + "\n".join(lineas) + f"\n{footer}\n"

# =========================================================
# 3. LÓGICA DE LA APLICACIÓN
# =========================================================
st.set_page_config(page_title="Gestión Maquinaria", layout="wide")
st.title("🚜 Control de Mantenimiento")

@st.cache_resource
def conectar_google():
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        info = CREDS_INFO.copy()
        # Aquí ocurre la magia: limpiamos la llave antes de usarla
        info["private_key"] = reconstruir_llave_pem(LLAVE_BRUTA)
        
        creds = Credentials.from_service_account_info(info, scopes=scope)
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"❌ Error de Autenticación: {e}")
        return None

cliente = conectar_google()

if cliente:
    try:
        hoja = cliente.open_by_key(ID_HOJA).sheet1
        st.sidebar.success("✅ Sistema Online")
        
        # Leer datos
        df = pd.DataFrame(hoja.get_all_records())

        # Botón de Gmail
        if st.button("🔄 Sincronizar"):
            with st.spinner("Buscando correos..."):
                imap = imaplib.IMAP4_SSL("imap.gmail.com")
                imap.login(EMAIL_USUARIO, EMAIL_PASSWORD)
                imap.select("INBOX")
                _, data = imap.search(None, 'ALL')
                
                existentes = df['id'].astype(str).tolist() if not df.empty else []
                nuevos_filas = []
                
                for m_id in reversed(data[0].split()[-10:]):
                    if m_id.decode() not in existentes:
                        _, m_data = imap.fetch(m_id, "(RFC822)")
                        msg = email.message_from_bytes(m_data[0][1])
                        asunto, enc = decode_header(msg.get("Subject", "Sin Asunto"))[0]
                        if isinstance(asunto, bytes): asunto = asunto.decode(enc or "utf-8")
                        nuevos_filas.append([m_id.decode(), asunto, msg.get("From"), ""])
                
                if nuevos_filas:
                    hoja.append_rows(nuevos_filas)
                    st.success(f"Se agregaron {len(nuevos_filas)} reportes.")
                    st.rerun()
                imap.logout()

        # Mostrar para editar
        if not df.empty:
            df['comentario'] = df['comentario'].fillna("").astype(str)
            pendientes = df[df['comentario'] == ""]
            
            for idx, row in pendientes.iterrows():
                with st.expander(f"⚙️ Reporte: {row['asunto']}"):
                    sol = st.text_area("Solución:", key=f"s_{row['id']}")
                    if st.button("Guardar ✅", key=f"b_{row['id']}"):
                        hoja.update_cell(idx + 2, 4, sol)
                        st.rerun()
        else:
            st.info("Sin datos. Presiona sincronizar.")

    except Exception as e:
        st.error(f"Error de lectura: {e}")
