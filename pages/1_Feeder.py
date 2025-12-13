import streamlit as st
import pandas as pd

st.title("Feeder de Lista de Precios")

PRECIO_COL = "PRECIO_LISTA"

archivo = st.file_uploader("Sube la lista de precios (Excel)", type=["xlsx"])
nombre_lista = st.text_input("Nombre de la lista")

if archivo and nombre_lista:
    df = pd.read_excel(archivo)

    # Normalización
    df[PRECIO_COL] = pd.to_numeric(df[PRECIO_COL], errors="coerce")
    df = df[df[PRECIO_COL].notna()]

    # Sustituir catálogo completamente
    st.session_state.catalogo = df.copy()
    st.session_state.lista_activa = nombre_lista

    st.success(f"Lista '{nombre_lista}' cargada correctamente ({len(df)} productos).")

if "catalogo" in st.session_state:
    st.info(
        f"Lista activa: {st.session_state.get('lista_activa')} | "
        f"Productos: {len(st.session_state.catalogo)}"
    )
