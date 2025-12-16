import streamlit as st
import pandas as pd
import re
import unicodedata

st.title("Feeder de Lista de Precios")

PRECIO_COL = "PRECIO_LISTA"

# Inicializar listas guardadas
if "listas_guardadas" not in st.session_state:
    st.session_state.listas_guardadas = {}

def _norm(s: str) -> str:
    s = str(s).strip()
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    s = s.upper()
    s = re.sub(r"\s+", "_", s)
    s = re.sub(r"[^A-Z0-9_]", "", s)
    return s

def resolve_column(df, candidates):
    # candidates: list[str] de nombres esperados (en crudo)
    norm_map = {_norm(c): c for c in df.columns}
    for cand in candidates:
        key = _norm(cand)
        if key in norm_map:
            return norm_map[key]
    return None

# --- Resolver columna de precio sin asumir ---
PRICE_CANDIDATES = [
    "PRECIO_LISTA", "PRECIO LISTA", "PRECIO", "PRECIO_MXN", "PRECIO MXN",
    "LIST_PRICE", "LISTPRICE", "MSRP", "PVP", "PRECIO PUBLICO"
]

# --- CARGAR NUEVA LISTA ---
st.subheader("📥 Cargar nueva lista")

archivo = st.file_uploader("Sube la lista de precios (Excel)", type=["xlsx"])
nombre_lista = st.text_input("Nombre de la lista")

if archivo and nombre_lista:
    df = pd.read_excel(archivo)

    precio_col_real = resolve_column(df, PRICE_CANDIDATES)

    if not precio_col_real:
        st.error(
            "No encontré la columna de precio en tu Excel. "
            "Columnas detectadas: " + ", ".join(map(str, df.columns))
        )
        st.stop()

    df[precio_col_real] = pd.to_numeric(df[precio_col_real], errors="coerce")
    df = df[df[precio_col_real].notna()].copy()

    # Si quieres estandarizar internamente:
    df["PRECIO_LISTA"] = df[precio_col_real]

    # Guardar en el diccionario de listas
    st.session_state.listas_guardadas[nombre_lista] = df.copy()
    st.session_state.catalogo = df.copy()
    st.session_state.lista_activa = nombre_lista

    st.success(f"Lista '{nombre_lista}' cargada y guardada ({len(df)} productos).")

# --- SELECCIONAR LISTA EXISTENTE ---
if st.session_state.listas_guardadas:
    st.subheader("📋 Seleccionar lista guardada")
    
    opciones_listas = list(st.session_state.listas_guardadas.keys())
    lista_seleccionada = st.selectbox(
        "Listas disponibles", 
        opciones_listas,
        index=opciones_listas.index(st.session_state.get("lista_activa")) 
              if st.session_state.get("lista_activa") in opciones_listas else 0
    )
    
    if st.button("Activar lista seleccionada"):
        st.session_state.catalogo = st.session_state.listas_guardadas[lista_seleccionada].copy()
        st.session_state.lista_activa = lista_seleccionada
        st.success(f"Lista '{lista_seleccionada}' activada.")
        st.rerun()

if "catalogo" in st.session_state:
    st.info(
        f"📌 Lista activa: {st.session_state.get('lista_activa')} | "
        f"Productos: {len(st.session_state.catalogo)}"
    )
