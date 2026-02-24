import streamlit as st
from streamlit_gsheets import GSheetsConnection
import imaplib
import email
from email.header import decode_header
import pandas as pd

# --- CONFIGURACIÓN ---
ID_HOJA = "1fdCf2HsS8KKkuqrJ8DwiDednW8lwnz7-WfvuVJwQnBo"
EMAIL_USUARIO = "kiritokayabaki@gmail.com" 
EMAIL_PASSWORD = "wkpn qayc mtqj ucut"

st.set_page_config(page_title="Gestión Maquinaria", layout="wide")

# --- CONEXIÓN ---
try:
    # Usamos la conexión oficial de Streamlit
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(spreadsheet=ID_HOJA, worksheet="Sheet1", ttl=0)
    error_pem = False
except Exception as e:
    st.error(f"⚠️ Error de Conexión: {e}")
    st.info("Revisa que tus Secrets tengan el formato correcto.")
    error_pem = True
    df = pd.DataFrame()

# --- FUNCIONES ---
def buscar_correos():
    try:
        imap = imaplib.IMAP4_SSL("imap.gmail.com")
        imap.login(EMAIL_USUARIO, EMAIL_PASSWORD)
        imap.select("INBOX")
        _, mensajes = imap.search(None, 'ALL')
        ids = mensajes[0].split()
        
        lista = []
        for i in reversed(ids[-5:]): # Últimos 5
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

# --- INTERFAZ ---
st.title("🚜 Panel de Mantenimiento")

if not error_pem:
    if st.button("🔄 Buscar Reportes Nuevos"):
        nuevos = buscar_correos()
        if nuevos:
            df_final = pd.concat([pd.DataFrame(nuevos), df], ignore_index=True)
            conn.update(spreadsheet=ID_HOJA, worksheet="Sheet1", data=df_final)
            st.success("¡Nuevos reportes agregados!")
            st.rerun()
        else:
            st.info("No hay correos nuevos.")

    if not df.empty:
        df['comentario'] = df['comentario'].fillna("")
        pendientes = df[df['comentario'] == ""]
        
        st.subheader(f"Reportes Pendientes ({len(pendientes)})")
        for idx, row in pendientes.iterrows():
            with st.expander(f"Asunto: {row['asunto']}"):
                st.write(f"**De:** {row['de']}")
                solucion = st.text_area("Solución:", key=f"s_{row['id']}")
                if st.button("Finalizar ✅", key=f"b_{row['id']}"):
                    df.loc[df['id'] == row['id'], 'comentario'] = solucion
                    conn.update(spreadsheet=ID_HOJA, worksheet="Sheet1", data=df)
                    st.rerun()
    else:
        st.write("Hoja de cálculo vacía. Envía un correo y presiona Sincronizar.")
