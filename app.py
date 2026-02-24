import streamlit as st
from streamlit_gsheets import GSheetsConnection
import imaplib
import email
from email.header import decode_header
import pandas as pd

# CONFIGURACIÓN
ID_HOJA = "1fdCf2HsS8KKkuqrJ8DwiDednW8lwnz7-WfvuVJwQnBo"
EMAIL_USUARIO = "kiritokayabaki@gmail.com" 
EMAIL_PASSWORD = "wkpn qayc mtqj ucut"

st.set_page_config(page_title="Gestión Maquinaria", layout="wide")

# CONEXIÓN CON LIMPIEZA AUTOMÁTICA
try:
    # Corregimos la llave en tiempo real si el sistema se confunde con las barras
    if "connections" in st.secrets and "gsheets" in st.secrets.connections:
        raw_key = st.secrets.connections.gsheets.private_key
        # Forzamos a que las barras invertidas se procesen correctamente
        if "\\n" in raw_key:
            st.secrets.connections.gsheets.private_key = raw_key.replace("\\n", "\n")

    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(spreadsheet=ID_HOJA, worksheet="Sheet1", ttl=0)
    st.sidebar.success("✅ Conectado")
    error_bloqueo = False
except Exception as e:
    st.error(f"❌ Error de Conexión: {e}")
    error_bloqueo = True
    df = pd.DataFrame()

# FUNCIÓN DE GMAIL
def sincronizar_gmail():
    try:
        imap = imaplib.IMAP4_SSL("imap.gmail.com")
        imap.login(EMAIL_USUARIO, EMAIL_PASSWORD)
        imap.select("INBOX")
        _, mensajes = imap.search(None, 'ALL')
        ids = mensajes[0].split()
        
        lista_nuevos = []
        for i in reversed(ids[-5:]):
            idx_str = i.decode()
            if df.empty or idx_str not in df['id'].astype(str).values:
                res, msg = imap.fetch(i, "(RFC822)")
                for respuesta in msg:
                    if isinstance(respuesta, tuple):
                        mensaje = email.message_from_bytes(respuesta[1])
                        asunto, enc = decode_header(mensaje.get("Subject", "Sin Asunto"))[0]
                        if isinstance(asunto, bytes): asunto = asunto.decode(enc or "utf-8")
                        lista_nuevos.append({"id": idx_str, "asunto": asunto, "de": mensaje.get("From"), "comentario": ""})
        imap.logout()
        return lista_nuevos
    except: return []

# INTERFAZ
st.title("🚜 Gestión de Maquinaria")

if not error_bloqueo:
    if st.button("🔄 Buscar Reportes Nuevos"):
        nuevos_datos = sincronizar_gmail()
        if nuevos_datos:
            df_final = pd.concat([pd.DataFrame(nuevos_datos), df], ignore_index=True)
            conn.update(spreadsheet=ID_HOJA, worksheet="Sheet1", data=df_final)
            st.rerun()
        else:
            st.info("Todo al día.")

    if not df.empty:
        df['comentario'] = df['comentario'].fillna("")
        pendientes = df[df['comentario'] == ""]
        st.subheader(f"Pendientes: {len(pendientes)}")
        for idx, row in pendientes.iterrows():
            with st.expander(f"Reporte: {row['asunto']}"):
                sol = st.text_area("Solución:", key=f"t_{row['id']}")
                if st.button("Guardar ✅", key=f"b_{row['id']}"):
                    df.loc[df['id'] == row['id'], 'comentario'] = sol
                    conn.update(spreadsheet=ID_HOJA, worksheet="Sheet1", data=df)
                    st.rerun()
