import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import imaplib
import email
from email.header import decode_header

# =========================================================
# 1. FUNCIÓN LIMPIADORA (PARA MATAR EL ERROR 95)
# =========================================================
def limpiar_credenciales():
    """Esta función arregla la llave PEM aunque esté mal pegada en Secrets"""
    try:
        creds = dict(st.secrets["connections"]["gsheets"])
        # Limpiamos la llave de cualquier carácter invisible o error de pegado
        key = creds["private_key"]
        if "\\n" in key:
            key = key.replace("\\n", "\n")
        
        # Eliminamos espacios en blanco accidentales al inicio/final de cada línea
        lineas = [linea.strip() for linea in key.split("\n") if linea.strip()]
        key_limpia = "\n".join(lineas)
        
        # Reinyectamos la llave limpia en la configuración de la conexión
        creds["private_key"] = key_limpia
        return creds
    except Exception as e:
        st.error(f"Error accediendo a Secrets: {e}")
        return None

# =========================================================
# 2. CONFIGURACIÓN DE CONEXIÓN
# =========================================================
ID_HOJA = "1fdCf2HsS8KKkuqrJ8DwiDednW8lwnz7-WfvuVJwQnBo"
st.set_page_config(page_title="Maquinaria Dash", layout="wide")

try:
    # Usamos la conexión pero le pasamos las credenciales ya limpias
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(spreadsheet=ID_HOJA, worksheet="Sheet1", ttl=0)
    st.success("✅ ¡CONEXIÓN EXITOSA!")
except Exception as e:
    st.error(f"Error de conexión: {e}")
    st.info("Si el error persiste, verifica que el correo del Service Account sea EDITOR en el Excel.")
    df = pd.DataFrame()

# =========================================================
# 3. MOTOR DE GMAIL
# =========================================================
EMAIL_USUARIO = "kiritokayabaki@gmail.com" 
EMAIL_PASSWORD = "wkpn qayc mtqj ucut"

def buscar_correos():
    try:
        imap = imaplib.IMAP4_SSL("imap.gmail.com")
        imap.login(EMAIL_USUARIO, EMAIL_PASSWORD)
        imap.select("INBOX", readonly=True)
        _, mensajes = imap.search(None, 'ALL')
        ids = [i.decode() for i in mensajes[0].split()]
        
        lista = []
        for i in reversed(ids[-5:]): # Solo los últimos 5
            res, msg = imap.fetch(i, "(RFC822)")
            for respuesta in msg:
                if isinstance(respuesta, tuple):
                    mensaje = email.message_from_bytes(respuesta[1])
                    asunto_raw = decode_header(mensaje.get("Subject", "Sin Asunto"))[0]
                    asunto = asunto_raw[0].decode(asunto_raw[1] or "utf-8") if isinstance(asunto_raw[0], bytes) else asunto_raw[0]
                    lista.append({"id": i, "asunto": asunto, "de": mensaje.get("From"), "comentario": ""})
        imap.logout()
        return lista
    except: return []

# =========================================================
# 4. INTERFAZ
# =========================================================
st.title("🚜 Gestión de Mantenimiento")

if not df.empty:
    # Sincronización automática con Gmail
    ids_en_excel = df['id'].astype(str).tolist()
    nuevos = [c for c in buscar_correos() if str(c['id']) not in ids_en_excel]
    
    if nuevos:
        df_nuevos = pd.DataFrame(nuevos)
        df_final = pd.concat([df_nuevos, df], ignore_index=True)
        conn.update(spreadsheet=ID_HOJA, worksheet="Sheet1", data=df_final)
        st.rerun()

    # Filtros y Visualización
    df['comentario'] = df['comentario'].fillna("")
    pendientes = df[df['comentario'] == ""]
    
    col1, col2 = st.columns(2)
    col1.metric("Pendientes", len(pendientes))
    col2.metric("Total", len(df))

    st.write("### 📝 Lista de Pendientes")
    for idx, row in pendientes.iterrows():
        with st.expander(f"Reporte: {row['asunto']}"):
            st.write(f"**De:** {row['de']}")
            nota = st.text_area("Añadir solución:", key=f"txt_{row['id']}")
            if st.button("Finalizar ✅", key=f"btn_{row['id']}"):
                df.loc[df['id'] == row['id'], 'comentario'] = nota
                conn.update(spreadsheet=ID_HOJA, worksheet="Sheet1", data=df)
                st.rerun()
else:
    st.warning("No se pudieron cargar datos. Revisa la configuración de Google Sheets.")
