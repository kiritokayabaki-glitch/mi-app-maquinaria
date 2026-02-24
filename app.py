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

st.set_page_config(page_title="Control de Maquinaria", layout="wide")

# 1. CONEXIÓN A GOOGLE SHEETS
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(spreadsheet=ID_HOJA, worksheet="Sheet1", ttl=0)
    st.sidebar.success("✅ Conectado a Google Sheets")
except Exception as e:
    st.error(f"Error de conexión: {e}")
    df = pd.DataFrame(columns=["id", "asunto", "de", "comentario"])

# 2. FUNCIÓN PARA BUSCAR CORREOS NUEVOS
def sincronizar_correos():
    try:
        imap = imaplib.IMAP4_SSL("imap.gmail.com")
        imap.login(EMAIL_USUARIO, EMAIL_PASSWORD)
        imap.select("INBOX")
        _, mensajes = imap.search(None, 'ALL')
        ids = mensajes[0].split()
        
        lista_nuevos = []
        # Ver los últimos 5 correos
        for i in reversed(ids[-5:]):
            idx_str = i.decode()
            # Si el ID del correo no está en nuestro Excel, es nuevo
            if df.empty or idx_str not in df['id'].astype(str).values:
                res, msg = imap.fetch(i, "(RFC822)")
                for respuesta in msg:
                    if isinstance(respuesta, tuple):
                        mensaje = email.message_from_bytes(respuesta[1])
                        asunto, encoding = decode_header(mensaje.get("Subject", "Sin Asunto"))[0]
                        if isinstance(asunto, bytes): asunto = asunto.decode(encoding or "utf-8")
                        
                        lista_nuevos.append({
                            "id": idx_str,
                            "asunto": asunto,
                            "de": mensaje.get("From"),
                            "comentario": ""
                        })
        imap.logout()
        return lista_nuevos
    except Exception as e:
        st.sidebar.error(f"Error Gmail: {e}")
        return []

# 3. LÓGICA DE ACTUALIZACIÓN
st.title("🚜 Gestión de Mantenimiento")

# Botón para forzar actualización
if st.button("🔄 Sincronizar nuevos reportes"):
    nuevos = sincronizar_correos()
    if nuevos:
        df_actualizado = pd.concat([pd.DataFrame(nuevos), df], ignore_index=True)
        conn.update(spreadsheet=ID_HOJA, worksheet="Sheet1", data=df_actualizado)
        st.success(f"Se encontraron {len(nuevos)} reportes nuevos.")
        st.rerun()
    else:
        st.info("No hay correos nuevos.")

# 4. INTERFAZ DE TRABAJO
if not df.empty:
    df['comentario'] = df['comentario'].fillna("")
    pendientes = df[df['comentario'] == ""]
    
    st.subheader(f"Pendientes de revisión: {len(pendientes)}")
    
    for idx, row in pendientes.iterrows():
        with st.expander(f"Reporte: {row['asunto']} (Enviado por: {row['de']})"):
            solucion = st.text_area("Escribe la solución técnica:", key=f"sol_{row['id']}")
            if st.button("Marcar como Reparado ✅", key=f"btn_{row['id']}"):
                df.loc[df['id'] == row['id'], 'comentario'] = solucion
                conn.update(spreadsheet=ID_HOJA, worksheet="Sheet1", data=df)
                st.balloons()
                st.rerun()
else:
    st.write("No hay datos para mostrar. Asegúrate de que el Excel tenga las columnas: id, asunto, de, comentario.")
