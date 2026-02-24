import streamlit as st
from streamlit_gsheets import GSheetsConnection
import imaplib
import email
from email.header import decode_header
import pandas as pd
import re

# =========================================================
# 1. LA LLAVE VA AQUÍ (DIRECTA Y LIMPIA)
# =========================================================
# Pega tu llave aquí adentro, no importa si tiene saltos de línea
LLAVE_JSON_BRUTA = """
-----BEGIN PRIVATE KEY-----
PEGA_AQUI_TU_LLAVE_COMPLETA
-----END PRIVATE KEY-----
"""

def limpiar_pem(texto):
    # Quitamos espacios y puntos invisibles que causan el error (56, 46)
    limpio = texto.strip()
    # Si la pegaste con \n literales, los convertimos a saltos reales
    limpio = limpio.replace("\\n", "\n")
    return limpio

# =========================================================
# 2. CONFIGURACIÓN DE CONEXIÓN
# =========================================================
ID_HOJA = "1fdCf2HsS8KKkuqrJ8DwiDednW8lwnz7-WfvuVJwQnBo"
EMAIL_USUARIO = "kiritokayabaki@gmail.com" 
EMAIL_PASSWORD = "wkpn qayc mtqj ucut"

st.set_page_config(page_title="Gestión Maquinaria", layout="wide")

try:
    # Inyectamos la llave limpia manualmente en los secretos de la sesión
    if "connections" in st.secrets:
        st.secrets.connections.gsheets["private_key"] = limpiar_pem(LLAVE_JSON_BRUTA)
    
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(spreadsheet=ID_HOJA, worksheet="Sheet1", ttl=0)
    st.sidebar.success("✅ Conexión Exitosa")
    error_app = False
except Exception as e:
    st.error(f"❌ Error crítico: {e}")
    st.info("Asegúrate de haber pegado la llave correctamente en el código.")
    error_app = True
    df = pd.DataFrame()

# =========================================================
# 3. MOTOR DE GMAIL Y LÓGICA
# =========================================================
def sincronizar_gmail():
    try:
        imap = imaplib.IMAP4_SSL("imap.gmail.com")
        imap.login(EMAIL_USUARIO, EMAIL_PASSWORD)
        imap.select("INBOX")
        _, mensajes = imap.search(None, 'ALL')
        ids = mensajes[0].split()
        lista = []
        for i in reversed(ids[-5:]):
            idx_str = i.decode()
            if df.empty or idx_str not in df['id'].astype(str).values:
                res, msg = imap.fetch(i, "(RFC822)")
                for respuesta in msg:
                    if isinstance(respuesta, tuple):
                        mensaje = email.message_from_bytes(respuesta[1])
                        asunto, enc = decode_header(mensaje.get("Subject", "Sin Asunto"))[0]
                        if isinstance(asunto, bytes): asunto = asunto.decode(enc or "utf-8")
                        lista.append({"id": idx_str, "asunto": asunto, "de": mensaje.get("From"), "comentario": ""})
        imap.logout()
        return lista
    except: return []

st.title("🚜 Control de Reportes")

if not error_app:
    if st.button("🔄 Sincronizar"):
        nuevos = sincronizar_gmail()
        if nuevos:
            df_final = pd.concat([pd.DataFrame(nuevos), df], ignore_index=True)
            conn.update(spreadsheet=ID_HOJA, worksheet="Sheet1", data=df_final)
            st.rerun()
        else:
            st.info("No hay novedades.")

    if not df.empty:
        df['comentario'] = df['comentario'].fillna("")
        pendientes = df[df['comentario'] == ""]
        for idx, row in pendientes.iterrows():
            with st.expander(f"Reporte: {row['asunto']}"):
                sol = st.text_area("Solución:", key=f"t_{row['id']}")
                if st.button("Guardar ✅", key=f"b_{row['id']}"):
                    df.loc[df['id'] == row['id'], 'comentario'] = sol
                    conn.update(spreadsheet=ID_HOJA, worksheet="Sheet1", data=df)
                    st.rerun()
