import streamlit as st

st.set_page_config(page_title="Cotizador", layout="wide")

st.sidebar.title("Cotizador Comercial")

st.sidebar.page_link("pages/1_Feeder.py", label="1. Feeder de Listas")
st.sidebar.page_link("pages/2_Cotizador.py", label="2. Cotizador")
