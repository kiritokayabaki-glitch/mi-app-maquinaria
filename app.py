import streamlit as st
import pandas as pd
from datetime import date

# Configuración con el color de tu app
st.set_page_config(page_title="New App", layout="centered")

# Estilo CSS para imitar a AppSheet (Botones naranjas y bordes redondeados)
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    .stButton>button { width: 100%; background-color: #f39c12; color: white; border-radius: 10px; border: none; height: 50px; }
    .stHeader { background-color: #f39c12; padding: 10px; color: white; border-radius: 5px; }
    [data-testid="stMetricValue"] { color: #f39c12; }
    </style>
    """, unsafe_allow_html=True)

# Encabezado como en tu captura
st.markdown("<div class='stHeader'><h2 style='text-align: center; margin:0;'>🚜 New App</h2></div>", unsafe_allow_html=True)

# Simulación de la barra de navegación de AppSheet (Eventos, Ingreso, Reporte)
menu = st.columns(3)
with menu[0]:
    btn_eventos = st.button("📅 Eventos")
with menu[1]:
    btn_ingreso = st.button("📋 Ingreso")
with menu[2]:
    btn_reporte = st.button("📄 Reporte")

st.divider()

# Lógica de las pantallas
if btn_ingreso:
    st.subheader("Ingreso De Servicio")
    with st.container():
        usuario = st.text_input("USUARIO", value="kiritokayabaki@gmail.com")
        fecha = st.date_input("FECHA", date.today())
        estado = st.selectbox("ESTADO", ["Pendiente", "En Proceso", "Completado"])
        st.button("GUARDAR REGISTRO")

elif btn_reporte:
    st.subheader("Reporte de servicios")
    # Tarjeta visual estilo AppSheet
    st.info(f"Fecha del reporte: {date.today()}")
    st.write("**Detalle de Maquinaria:**")
    col1, col2 = st.columns(2)
    col1.write("🛠 **Equipo:** Montacargas")
    col2.write("🔢 **Serie:** A234X0567")

else:
    # Pantalla por defecto (Eventos/Home)
    st.subheader("Vista por FECHA")
    st.write("2/23/2026")
    st.markdown("""
    <div style="background-color: white; padding: 15px; border-left: 5px solid #f39c12; border-radius: 5px; box-shadow: 2px 2px 5px rgba(0,0,0,0.1);">
        <strong>Servicio Preventivo</strong><br>
        <small>Estado: Pendiente | Horómetro: 1200 hrs</small>
    </div>
    """, unsafe_allow_html=True)
