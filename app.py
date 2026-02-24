import streamlit as st
import imaplib
import email
from email.header import decode_header

# --- CONFIGURACIÓN ---
EMAIL_USUARIO = "kiritokayabaki@gmail.com" 
EMAIL_PASSWORD = "wkpn qayc mtqj ucut"

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
            tipo = parte.get_content_type()
            if tipo == "text/plain":
                try:
                    cuerpo = parte.get_payload(decode=True).decode("utf-8", errors="replace")
                    break
                except: pass
    else:
        try: cuerpo = mensaje.get_payload(decode=True).decode("utf-8", errors="replace")
        except: pass
    return cuerpo[:500] + "..." if len(cuerpo) > 500 else cuerpo

def leer_correos():
    try:
        imap = imaplib.IMAP4_SSL("imap.gmail.com")
        imap.login(EMAIL_USUARIO, EMAIL_PASSWORD)
        imap.select("INBOX")
        status, mensajes = imap.search(None, 'ALL')
        ids = mensajes[0].split()
        lista = []
        for i in reversed(ids[-8:]):
            res, msg = imap.fetch(i, "(RFC822)")
            for respuesta in msg:
                if isinstance(respuesta, tuple):
                    mensaje = email.message_from_bytes(respuesta[1])
                    asunto_raw = decode_header(mensaje["Subject"])[0]
                    asunto = decodificar_texto(asunto_raw[0], asunto_raw[1])
                    contenido = obtener_cuerpo(mensaje)
                    lista.append({"Asunto": asunto, "De": mensaje.get("From"), "Cuerpo": contenido})
        imap.logout()
        return lista
    except Exception as e: return f"Error: {e}"

# --- INTERFAZ ---
st.set_page_config(page_title="Gestión Maquinaria", layout="wide")
st.title("🚜 Panel de Inspección de Maquinaria")

if "lista_correos" not in st.session_state:
    st.session_state.lista_correos = []

if st.button("🔄 Sincronizar Órdenes de Servicio"):
    with st.spinner("Cargando servicios de Gmail..."):
        st.session_state.lista_correos = leer_correos()

if st.session_state.lista_correos:
    for idx, item in enumerate(st.session_state.lista_correos):
        with st.expander(f"📋 ORDEN: {item['Asunto']}", expanded=True):
            col_info, col_registro = st.columns([1, 1])
            
            with col_info:
                st.subheader("Información del Servicio")
                st.write(f"**Solicitante:** {item['De']}")
                st.info(f"**Instrucciones:**\n{item['Cuerpo']}")
            
            with col_registro:
                st.subheader("Registro de Atención")
                # LÍNEA CORREGIDA AQUÍ ABAJO:
                comentario = st.text_area("Comentarios del Técnico:", key=f"c_{idx}", placeholder="Escribe aquí el reporte...")
                
                if comentario.strip():
                    st.success("🟢 ESTADO: ATENDIDA")
                else:
                    st.error("🔴 ESTADO: PENDIENTE")
                
                st.write("**Evidencia Visual:**")
                col_img1, col_img2 = st.columns(2)
                with col_img1:
                    foto_antes = st.file_uploader("🖼️ Anteriormente-Imagen", type=['png', 'jpg', 'jpeg'], key=f"img_ant_{idx}")
                    if foto_antes: st.image(foto_antes, caption="Vista Anterior")
                
                with col_img2:
                    foto_despues = st.file_uploader("📸 Actual-Imagen", type=['png', 'jpg', 'jpeg'], key=f"img_act_{idx}")
                    if foto_despues: st.image(foto_despues, caption="Vista Actual")
                
                if st.button("💾 Guardar Reporte Final", key=f"btn_{idx}"):
                    if comentario:
                        st.balloons()
                        st.success(f"Reporte de '{item['Asunto']}' listo para procesar.")
                    else:
                        st.warning("Agrega un comentario antes de guardar.")
            st.divider()
