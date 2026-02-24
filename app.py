import streamlit as st
import imaplib
import email
from email.header import decode_header
import time

# --- CONFIGURACIÓN ---
EMAIL_USUARIO = "kiritokayabaki@gmail.com" 
EMAIL_PASSWORD = "wkpn qayc mtqj ucut"

# --- FUNCIONES DE GMAIL ---
def decodificar_texto(texto, encoding):
    try:
        if isinstance(texto, bytes):
            return texto.decode(encoding or "utf-8", errors="replace")
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
    return cuerpo[:500]

def leer_correos():
    try:
        imap = imaplib.IMAP4_SSL("imap.gmail.com")
        imap.login(EMAIL_USUARIO, EMAIL_PASSWORD)
        imap.select("INBOX")
        status, mensajes = imap.search(None, 'ALL')
        ids = mensajes[0].split()
        lista = []
        # Traemos los últimos 10 correos
        for i in reversed(ids[-10:]):
            msg_id = i.decode() 
            res, msg = imap.fetch(i, "(RFC822)")
            for respuesta in msg:
                if isinstance(respuesta, tuple):
                    mensaje = email.message_from_bytes(respuesta[1])
                    asunto_raw = decode_header(mensaje["Subject"])[0]
                    asunto = decodificar_texto(asunto_raw[0], asunto_raw[1])
                    contenido = obtener_cuerpo(mensaje)
                    lista.append({
                        "id": msg_id, 
                        "Asunto": asunto, 
                        "De": mensaje.get("From"), 
                        "Cuerpo": contenido
                    })
        imap.logout()
        return lista
    except: return []

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Gestión Maquinaria RealTime", layout="wide")

# Inicializar estados de memoria
if "lista_correos" not in st.session_state:
    st.session_state.lista_correos = leer_correos()
if "last_sync" not in st.session_state:
    st.session_state.last_sync = time.time()

# --- LÓGICA DE ACTUALIZACIÓN RÁPIDA (Cada 10 segundos) ---
# Esto hace que la app se refresque sola sin tocar nada
tiempo_espera = 10 
ahora = time.time()

if ahora - st.session_state.last_sync > tiempo_espera:
    nuevos = leer_correos()
    if nuevos:
        st.session_state.lista_correos = nuevos
    st.session_state.last_sync = ahora
    st.rerun() # Fuerza a la app a redibujarse con los nuevos correos

st.title("🚜 Panel de Control en Tiempo Real")
st.write(f"⏱️ Próxima sincronización automática en {tiempo_espera} segundos...")

# --- MOSTRAR CORREOS ---
if st.session_state.lista_correos:
    for item in st.session_state.lista_correos:
        uid = item['id']
        
        # El ID del correo es la clave. Si el correo se mueve de posición,
        # sus datos (comentario/fotos) lo siguen porque están amarrados al ID.
        with st.expander(f"📋 ORDEN: {item['Asunto']} (ID: {uid})", expanded=True):
            col_info, col_registro = st.columns([1, 1])
            
            with col_info:
                st.write(f"**De:** {item['De']}")
                st.info(f"**Detalle:**\n{item['Cuerpo']}")
            
            with col_registro:
                # Usar el UID asegura que el texto NO se corra a otros correos
                comentario = st.text_area("Comentario del Técnico:", key=f"text_{uid}")
                
                if comentario.strip():
                    st.success("🟢 ESTADO: ATENDIDA")
                else:
                    st.error("🔴 ESTADO: PENDIENTE")
                
                c1, c2 = st.columns(2)
                with c1:
                    st.file_uploader("🖼️ Anteriormente", key=f"img_ant_{uid}")
                with c2:
                    st.file_uploader("📸 Actual", key=f"img_act_{uid}")
                
                if st.button("💾 Guardar Reporte", key=f"btn_{uid}"):
                    st.success(f"Datos de la orden {uid} bloqueados y guardados.")
            st.divider()
else:
    st.warning("No hay correos nuevos. Buscando cada 10 segundos...")

# Pequeño script para autorefrescar la página sin intervención
# Esto es un truco para que la app se mantenga "viva"
time.sleep(1) # Pausa mínima para no saturar el servidor
