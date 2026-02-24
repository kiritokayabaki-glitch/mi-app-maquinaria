import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import imaplib
import email
from email.header import decode_header
import plotly.graph_objects as go

# --- 1. CONEXIÓN SEGURA (Mantiene la sincronización) ---
def conectar_google():
    # Usa los Secrets que pegaremos en Streamlit Cloud (el JSON de Google)
    creds_dict = st.secrets["gcp_service_account"]
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    client = gspread.authorize(creds)
    return client.open_by_key("TU_ID_DE_HOJA_LARGO").sheet1

# --- 2. TUS FUNCIONES DE GMAIL (INTACTAS) ---
# Aquí van tus funciones: decodificar_texto, obtener_cuerpo, buscar_ids_recientes, leer_contenido_completo
# (Las que ya tienes funcionando perfectamente)

# --- 3. MOTOR DE SINCRONIZACIÓN (LA CLAVE DEL ÉXITO) ---
@st.fragment(run_every="10s")
def motor_principal():
    hoja = conectar_google()
    
    # A. Leer lo que hay en la nube
    datos_nube = pd.DataFrame(hoja.get_all_records())
    
    # B. Buscar correos nuevos en Gmail
    ids_recientes = buscar_ids_recientes()
    ids_en_hoja = datos_nube['id'].astype(str).tolist() if not datos_nube.empty else []
    
    ids_nuevos = [i for i in ids_recientes if str(i) not in ids_en_hoja]
    
    if ids_nuevos:
        nuevos_correos = leer_contenido_completo(ids_nuevos)
        for correo in nuevos_correos:
            # ESTO ES LO QUE NO FALLARÁ: Escribir el correo nuevo en la hoja
            hoja.insert_row([correo['id'], correo['asunto'], correo['de'], correo['cuerpo'], ""], 2)
        
        # Activar tu sonido y notificación
        play_notification_sound()
        st.toast("Nuevo reporte de maquinaria", icon="🚜")
        st.rerun()

    st.session_state.datos_app = datos_nube

motor_principal()

# --- 4. INTERFAZ VISUAL (Tus diseños, badges y colores) ---
# (Aquí sigue todo tu código de st.sidebar, los expanders, las fotos y la gráfica)
