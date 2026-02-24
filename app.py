import streamlit as st
from streamlit_gsheets import GSheetsConnection
import imaplib
import email
from email.header import decode_header
import plotly.graph_objects as go
import pandas as pd

# =========================================================
# 1. CONFIGURACIÓN DE CONEXIÓN
# =========================================================
ID_HOJA_CALCULO = "1fdCf2HsS8KKkuqrJ8DwiDednW8lwnz7-WfvuVJwQnBo" 

# Conexión forzada a los Secrets bajo el bloque [connections.gsheets]
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error(f"Error de configuración en Secrets: {e}")

def cargar_datos_nube():
    try:
        # ttl=0 asegura que si el mecánico actualiza en el taller, tú lo veas al instante
        return conn.read(spreadsheet=ID_HOJA_CALCULO, worksheet="Sheet1", ttl=0)
    except Exception as e:
        st.warning(f"Aún no hay datos en la nube o error de lectura: {e}")
        return pd.DataFrame(columns=["id", "asunto", "de", "cuerpo", "comentario"])

def guardar_datos_nube(df_nuevo):
    try:
        # El ID fuerza el uso de la Service Account configurada como EDITOR
        conn.update(spreadsheet=ID_HOJA_CALCULO, worksheet="Sheet1", data=df_nuevo)
        st.success("✅ ¡Base de datos sincronizada!")
    except Exception as e:
        st.error(f"Error al guardar: {e}")
        st.info("Revisa si el correo del Service Account es EDITOR en tu Google Sheet.")

# =========================================================
# 2. MOTOR DE GMAIL (RECEPCIÓN DE REPORTES)
# =========================================================
EMAIL_USUARIO = "kiritokayabaki@gmail.com" 
EMAIL_PASSWORD = "wkpn qayc mtqj ucut"

def play_notification_sound():
    audio_html = """<audio autoplay><source src="https://raw.githubusercontent.com/fernandoalonso-ds/sounds/main/notification.mp3" type="audio/mp3"></audio>"""
    st.components.v1.html(audio_html, height=0)

def decodificar_texto(texto, encoding):
    try:
        if isinstance(texto, bytes): return texto.decode(encoding or "utf-8", errors="replace")
        return str(texto)
    except: return "Texto no legible"

def obtener_cuerpo(mensaje):
    cuerpo = ""
    if mensaje.is_multipart():
        for parte in mensaje.walk():
            if parte.get_content_type() == "text/plain":
                try:
                    cuerpo = parte.get_payload(decode=True).decode("utf-8", errors="replace")
                    break
                except: pass
    else:
        try: cuerpo = mensaje.get_payload(decode=True).decode("utf-8", errors="replace")
        except: pass
    return cuerpo[:800]

def buscar_ids_recientes():
    try:
        imap = imaplib.IMAP4_SSL("imap.gmail.com")
        imap.login(EMAIL_USUARIO, EMAIL_PASSWORD)
        imap.select("INBOX", readonly=True)
        status, mensajes = imap.search(None, 'ALL')
        ids = [i.decode() for i in mensajes[0].split()]
        imap.logout()
        return ids[-20:]
    except: return []

def leer_contenido_completo(ids_a_buscar):
    try:
        imap = imaplib.IMAP4_SSL("imap.gmail.com")
        imap.login(EMAIL_USUARIO, EMAIL_PASSWORD)
        imap.select("INBOX", readonly=True)
        lista = []
        for i in reversed(ids_a_buscar):
            res, msg = imap.fetch(i, "(RFC822)")
            for respuesta in msg:
                if isinstance(respuesta, tuple):
                    mensaje = email.message_from_bytes(respuesta[1])
                    asunto_raw = decode_header(mensaje.get("Subject", "Sin Asunto"))[0]
                    asunto = decodificar_texto(asunto_raw[0], asunto_raw[1])
                    lista.append({
                        "id": i, 
                        "asunto": asunto, 
                        "de": mensaje.get("From"), 
                        "cuerpo": obtener_cuerpo(mensaje)
                    })
        imap.logout()
        return lista
    except: return []

# =========================================================
# 3. INTERFAZ Y LÓGICA
# =========================================================
st.set_page_config(page_title="Gestión Maquinaria Pro", layout="wide")

if "seccion" not in st.session_state: st.session_state.seccion = "Inicio"

# Motor de sincronización automática cada 10 segundos
@st.fragment(run_every="10s")
def motor_sincronizacion():
    df_actual = cargar_datos_nube()
    ids_recientes = buscar_ids_recientes()
    ids_en_nube = df_actual['id'].astype(str).tolist() if not df_actual.empty else []
    ids_nuevos = [i for i in ids_recientes if str(i) not in ids_en_nube]
    
    if ids_nuevos:
        nuevos_correos = leer_contenido_completo(ids_nuevos)
        df_nuevos = pd.DataFrame(nuevos_correos)
        df_nuevos['comentario'] = ""
        df_final = pd.concat([df_nuevos, df_actual], ignore_index=True)
        guardar_datos_nube(df_final)
        play_notification_sound()
        st.toast("🚜 Nuevo reporte detectado", icon="📥")
        st.rerun()
    
    st.session_state.datos_app = df_actual

motor_sincronizacion()

# --- PROCESAMIENTO DE DATOS ---
df = st.session_state.get('datos_app', pd.DataFrame(columns=["id", "asunto", "de", "cuerpo", "comentario"]))
df['comentario'] = df['comentario'].fillna("")
pendientes = df[df['comentario'] == ""]
atendidas = df[df['comentario'] != ""]

# --- BARRA LATERAL ---
with st.sidebar:
    st.title("🚜 Control")
    if st.button("🏠 Inicio"): st.session_state.seccion = "Inicio"
    if st.button(f"🔴 Pendientes ({len(pendientes)})"): st.session_state.seccion = "Pendientes"
    if st.button(f"🟢 Atendidas ({len(atendidas)})"): st.session_state.seccion = "Atendidas"

# --- VISTA INICIO ---
if st.session_state.seccion == "Inicio":
    st.title("📊 Resumen de Mantenimiento")
    c1, c2 = st.columns(2)
    c1.metric("Por atender", len(pendientes))
    c2.metric("Solucionados", len(atendidas))
    if not df.empty:
        fig = go.Figure(data=[go.Pie(labels=['Pendientes', 'Atendidas'], 
                                    values=[len(pendientes), len(atendidas)], 
                                    hole=.4, marker_colors=['#FF4B4B', '#00CC96'])])
        st.plotly_chart(fig)

# --- VISTA PENDIENTES ---
elif st.session_state.seccion == "Pendientes":
    st.header("⚠️ Reportes Críticos")
    for index, row in pendientes.iterrows():
        uid = str(row['id'])
        with st.expander(f"Reporte de: {row['de']} - {row['asunto']}"):
            st.info(f"**Mensaje:** {row['cuerpo']}")
            nota = st.text_area("Describa la solución técnica:", key=f"n_{uid}")
            if st.button("Marcar como Reparado ✅", key=f"btn_{uid}"):
                if nota.strip():
                    df.loc[df['id'].astype(str) == uid, 'comentario'] = nota
                    guardar_datos_nube(df)
                    st.rerun()
                else:
                    st.warning("Por favor, escribe un comentario antes de finalizar.")

# --- VISTA ATENDIDAS ---
elif st.session_state.seccion == "Atendidas":
    st.header("✅ Historial de Reparaciones")
    for index, row in atendidas.iterrows():
        uid = str(row['id'])
        with st.expander(f"Finalizado: {row['asunto']}"):
            st.write(f"**Reportado por:** {row['de']}")
            st.success(f"**Solución aplicada:** {row['comentario']}")
            if st.button("Reabrir Caso 🔓", key=f"re_{uid}"):
                df.loc[df['id'].astype(str) == uid, 'comentario'] = ""
                guardar_datos_nube(df)
                st.rerun()
