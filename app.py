import streamlit as st
import imaplib
import email
from email.header import decode_header

# --- CONFIGURACIÓN ---
EMAIL_USUARIO = "kiritokayabaki@gmail.com" 
EMAIL_PASSWORD = "wkpn qayc mtqj ucut"

# --- FUNCIONES DE DATOS ---
def buscar_ids_recientes():
    try:
        imap = imaplib.IMAP4_SSL("imap.gmail.com")
        imap.login(EMAIL_USUARIO, EMAIL_PASSWORD)
        imap.select("INBOX", readonly=True)
        status, mensajes = imap.search(None, 'ALL')
        ids = mensajes[0].split()
        ultimos_ids = [i.decode() for i in ids[-10:]]
        imap.logout()
        return ultimos_ids
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
                    asunto_raw = decode_header(mensaje["Subject"])[0]
                    asunto = str(asunto_raw[0])
                    lista.append({"id": i, "Asunto": asunto, "De": mensaje.get("From")})
        imap.logout()
        return lista
    except: return []

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Maquinaria Dash", layout="wide")

# Inicializar memoria
if "db_comentarios" not in st.session_state:
    st.session_state.db_comentarios = {}
if "ids_actuales" not in st.session_state:
    st.session_state.ids_actuales = []
if "lista_correos" not in st.session_state:
    st.session_state.lista_correos = []

# Sincronizador en segundo plano (Fragmento)
@st.fragment(run_every="20s")
def sincronizador_invisible():
    nuevos_ids = buscar_ids_recientes()
    if nuevos_ids != st.session_state.ids_actuales:
        st.session_state.ids_actuales = nuevos_ids
        st.session_state.lista_correos = leer_contenido_completo(nuevos_ids)
        st.rerun()

sincronizador_invisible()

# --- BARRA LATERAL (MENÚ) ---
st.sidebar.title("🚜 Menú Principal")
opcion = st.sidebar.radio("Ir a:", ["🏠 Inicio / Resumen", "🔴 Pendientes", "🟢 Atendidas", "📂 Todas las Órdenes"])

# Clasificar correos
pendientes = [c for c in st.session_state.lista_correos if not st.session_state.db_comentarios.get(c['id'], "").strip()]
atendidas = [c for c in st.session_state.lista_correos if st.session_state.db_comentarios.get(c['id'], "").strip()]

# --- LÓGICA DE PANTALLAS ---

if opcion == "🏠 Inicio / Resumen":
    st.title("📊 Resumen de Actividad")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total de Órdenes", len(st.session_state.lista_correos))
    with col2:
        st.metric("🔴 Pendientes", len(pendientes), delta_color="inverse")
    with col3:
        st.metric("🟢 Atendidas", len(atendidas))

    st.divider()
    
    c_pend, c_atend = st.columns(2)
    with c_pend:
        st.subheader("Últimas Pendientes")
        for p in pendientes[:3]: # Solo mostrar las 3 más recientes
            if st.button(f"Ir a: {p['Asunto']}", key=f"btn_p_{p['id']}"):
                st.info("Usa el menú de la izquierda para ver el detalle en 'Pendientes'")
                
    with c_atend:
        st.subheader("Recién Atendidas")
        for a in atendidas[:3]:
            st.write(f"✅ {a['Asunto']}")

elif opcion == "🔴 Pendientes":
    st.title("🔴 Órdenes Pendientes de Atención")
    if not pendientes:
        st.success("¡Buen trabajo! No hay órdenes pendientes.")
    else:
        for item in pendientes:
            with st.container(border=True):
                col1, col2 = st.columns([1, 1])
                with col1:
                    st.subheader(item['Asunto'])
                    st.write(f"Remitente: {item['De']}")
                with col2:
                    txt = st.text_area("Registrar Comentario:", key=f"t_{item['id']}")
                    if txt:
                        st.session_state.db_comentarios[item['id']] = txt
                        st.rerun() # Recarga para moverla a "Atendidas"
                    st.error("ESTADO: PENDIENTE")

elif opcion == "🟢 Atendidas":
    st.title("🟢 Órdenes Finalizadas")
    for item in atendidas:
        with st.expander(f"✅ {item['Asunto']}", expanded=False):
            st.write(f"**Comentario guardado:** {st.session_state.db_comentarios[item['id']]}")
            st.file_uploader("Actualizar Imagen", key=f"img_{item['id']}")

elif opcion == "📂 Todas las Órdenes":
    st.title("📂 Historial Completo")
    for item in st.session_state.lista_correos:
        estado = "🟢" if st.session_state.db_comentarios.get(item['id']) else "🔴"
        st.write(f"{estado} **{item['Asunto']}** - ID: {item['id']}")
