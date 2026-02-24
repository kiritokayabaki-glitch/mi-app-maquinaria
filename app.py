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
        return [i.decode() for i in ids[-15:]]
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
                    asunto = str(asunto_raw[0])
                    lista.append({"id": i, "Asunto": asunto, "De": mensaje.get("From")})
        imap.logout()
        return lista
    except: return []

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Maquinaria Dash Pro", layout="wide")

# --- CSS MEJORADO PARA LEGIBILIDAD ---
st.markdown("""
    <style>
    /* Estilo general de los botones del menú */
    .stButton > button {
        width: 100%;
        border-radius: 8px;
        height: 3.5em;
        background-color: #f0f2f6;
        color: #1f1f1f !important; /* Texto oscuro para que se lea bien */
        border: 1px solid #d1d5db;
        text-align: left;
        padding-left: 15px;
        font-weight: 600;
        font-size: 16px;
    }
    
    /* Efecto al pasar el mouse */
    .stButton > button:hover {
        background-color: #e5e7eb;
        border-color: #9ca3af;
    }

    /* Burbujas de contador (Badges) */
    .badge-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        width: 100%;
        margin-top: -48px; /* Ajuste para quedar sobre el botón */
        margin-bottom: 20px;
        padding: 0 15px;
        pointer-events: none; /* Para que el clic pase al botón de abajo */
    }
    
    .badge-text {
        font-weight: bold;
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 14px;
        color: #1f1f1f; /* Texto del número en oscuro */
        border: 1px solid rgba(0,0,0,0.1);
    }
    
    .bg-pendientes { background-color: #ffc1c1; }
    .bg-atendidas { background-color: #c1f2c1; }
    </style>
    """, unsafe_allow_html=True)

# Inicializar memoria
if "db_comentarios" not in st.session_state:
    st.session_state.db_comentarios = {}
if "lista_correos" not in st.session_state:
    st.session_state.lista_correos = leer_contenido_completo(buscar_ids_recientes())
if "seccion" not in st.session_state:
    st.session_state.seccion = "Inicio"

# --- LÓGICA DE FILTROS ---
pendientes = [c for c in st.session_state.lista_correos if not st.session_state.db_comentarios.get(c['id'], "").strip()]
atendidas = [c for c in st.session_state.lista_correos if st.session_state.db_comentarios.get(c['id'], "").strip()]

# --- BARRA LATERAL ---
with st.sidebar:
    st.markdown("### 🚜 Menú de Gestión")
    
    # Botón Inicio
    if st.button("🏠 Inicio", key="nav_home"):
        st.session_state.seccion = "Inicio"
    
    st.write("") # Espaciador

    # Botón Pendientes
    if st.button("🔴 Pendientes", key="nav_pend"):
        st.session_state.seccion = "Pendientes"
    st.markdown(f"""
        <div class="badge-container">
            <span></span>
            <span class="badge-text bg-pendientes">{len(pendientes)}</span>
        </div>
    """, unsafe_allow_html=True)

    # Botón Atendidas
    if st.button("🟢 Atendidas", key="nav_atend"):
        st.session_state.seccion = "Atendidas"
    st.markdown(f"""
        <div class="badge-container">
            <span></span>
            <span class="badge-text bg-atendidas">{len(atendidas)}</span>
        </div>
    """, unsafe_allow_html=True)

# --- PANTALLAS ---
if st.session_state.seccion == "Inicio":
    st.title("📊 Resumen de Tareas")
    col1, col2 = st.columns(2)
    col1.metric("Pendientes", len(pendientes))
    col2.metric("Atendidas", len(atendidas))
    st.info("Utilice el menú lateral para navegar entre las órdenes.")

elif st.session_state.seccion == "Pendientes":
    st.title("🔴 Órdenes por Atender")
    for item in pendientes:
        with st.container(border=True):
            st.subheader(item['Asunto'])
            st.write(f"**De:** {item['De']}")
            coment = st.text_area("Agregar nota de inspección", key=f"in_{item['id']}")
            if st.button("Marcar como Atendida ✅", key=f"sv_{item['id']}"):
                if coment.strip():
                    st.session_state.db_comentarios[item['id']] = coment
                    st.rerun()

elif st.session_state.seccion == "Atendidas":
    st.title("🟢 Historial de Atendidas")
    for item in atendidas:
        with st.expander(f"✅ {item['Asunto']}"):
            st.write(f"**Nota:** {st.session_state.db_comentarios.get(item['id'])}")
            if st.button("Reabrir", key=f"re_{item['id']}"):
                st.session_state.db_comentarios.pop(item['id'])
                st.rerun()
