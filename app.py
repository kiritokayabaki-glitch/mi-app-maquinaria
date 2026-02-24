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

# --- CONEXIÓN DIRECTA ---
try:
    # Inicializamos la conexión oficial
    conn = st.connection("gsheets", type=GSheetsConnection)
    # Intentamos leer la hoja inmediatamente
    df = conn.read(spreadsheet=ID_HOJA, worksheet="Sheet1", ttl=0)
    st.sidebar.success("✅ Conexión establecida")
    error_bloqueo = False
except Exception as e:
    st.error(f"❌ Error de Conexión: {e}")
    st.info("Revisa que en Secrets la private_key use comillas simples y contenga los \\n")
    error_bloqueo = True
    df = pd.DataFrame()

# --- FUNCIONES DE CORREO ---
def sincronizar_gmail():
    try:
        imap = imaplib.IMAP4_SSL("imap.gmail.com")
        imap.login(EMAIL_USUARIO, EMAIL_PASSWORD)
        imap.select("INBOX")
        _, mensajes = imap.search(None, 'ALL')
        ids = mensajes[0].split()
        
        lista_nuevos = []
        # Revisamos los últimos 5 para velocidad
        for i in reversed(ids[-5:]):
            idx_str = i.decode()
            # Si el ID no está en el Excel actual, es nuevo
            if df.empty or idx_str not in df['id'].astype(str).values:
                res, msg = imap.fetch(i, "(RFC822)")
                for respuesta in msg:
                    if isinstance(respuesta, tuple):
                        mensaje = email.message_from_bytes(respuesta[1])
                        asunto, enc = decode_header(mensaje.get("Subject", "Sin Asunto"))[0]
                        if isinstance(asunto, bytes): asunto = asunto.decode(enc or "utf-8")
                        
                        lista_nuevos.append({
                            "id": idx_str,
                            "asunto": asunto,
                            "de": mensaje.get("From"),
                            "comentario": ""
                        })
        imap.logout()
        return lista_nuevos
    except Exception as e:
        st.error(f"Error Gmail: {e}")
        return []

# --- INTERFAZ PRINCIPAL ---
st.title("🚜 Control de Reportes de Maquinaria")

if not error_bloqueo:
    # Botón de Sincronización
    if st.button("🔄 Sincronizar con Gmail"):
        nuevos_datos = sincronizar_gmail()
        if nuevos_datos:
            df_actualizado = pd.concat([pd.DataFrame(nuevos_datos), df], ignore_index=True)
            conn.update(spreadsheet=ID_HOJA, worksheet="Sheet1", data=df_actualizado)
            st.success("✅ Se agregaron nuevos reportes.")
            st.rerun()
        else:
            st.info("No hay reportes nuevos en el correo.")

    # Mostrar Datos
    if not df.empty:
        df['comentario'] = df['comentario'].fillna("")
        pendientes = df[df['comentario'] == ""]
        
        st.subheader(f"Reportes Pendientes: {len(pendientes)}")
        
        for idx, row in pendientes.iterrows():
            with st.expander(f"Reporte: {row['asunto']} | De: {row['de']}"):
                sol = st.text_area("Describa la reparación:", key=f"txt_{row['id']}")
                if st.button("Marcar como Reparado ✅", key=f"btn_{row['id']}"):
                    df.loc[df['id'] == row['id'], 'comentario'] = sol
                    conn.update(spreadsheet=ID_HOJA, worksheet="Sheet1", data=df)
                    st.balloons()
                    st.rerun()
    else:
        st.write("La base de datos está vacía. Usa el botón de sincronizar.")
