import streamlit as st
import pandas as pd
from graph_utils import grafica_aportacion_precio, grafica_aportacion_utilidad
from pdf_generator_reportlab import generar_pdf_horizontal
import numpy as np
import pandas as pd

def recalcular_cotizacion(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Asegurar numéricos
    for c in ["PRECIO_LISTA", "DESC_FAB_PCT", "MARGEN_PCT", "COSTO", "PRECIO_VENTA"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0.0)

    # 1) Costo = precio_lista * (1 - desc_fab)
    # desc_fab_pct viene como 30 para 30%
    df["COSTO"] = df["PRECIO_LISTA"] * (1.0 - (df["DESC_FAB_PCT"] / 100.0))

    # 2) Precio venta = costo / (1 - margen)
    denom = 1.0 - (df["MARGEN_PCT"] / 100.0)
    denom = denom.replace(0, np.nan)  # evita división entre cero
    df["PRECIO_VENTA"] = (df["COSTO"] / denom).fillna(0.0)

    # 3) Utilidad bruta = precio_venta - costo
    df["UTILIDAD_BRUTA"] = df["PRECIO_VENTA"] - df["COSTO"]

    return df

st.title("Cotizador Comercial")

if "catalogo" not in st.session_state:
    st.error("No hay lista cargada. Ve al Feeder.")
    st.stop()

catalogo = st.session_state.catalogo
st.info(f"Lista activa: {st.session_state.get('lista_activa')}")

# Inicializar líneas
if "lineas" not in st.session_state:
    st.session_state.lineas = pd.DataFrame(
        columns=[
            "SKU",
            "DESCRIPCION",
            "PRECIO_LISTA",
            "DESC_FAB_PCT",
            "COSTO",
            "MARGEN_PCT",
            "PRECIO_VENTA",
            "UTILIDAD_BRUTA"
        ]
    )

st.subheader("Seleccionar producto")

# Columnas reales del Excel
COL_CLASE = "CLASE"
COL_SUBCLASE = "SUBCLASE"
COL_PARTE = "NO. DE PARTE"
COL_MODELO = "MODELO"
COL_DESC = "DESCRIPCIÓN"
COL_PRECIO = "PRECIO\nMXN"

# -------- Dropdown 1: CLASE --------
opciones_clase = sorted(catalogo[COL_CLASE].dropna().unique())
sel_clase = st.selectbox("Clase", opciones_clase)

df_clase = catalogo[catalogo[COL_CLASE] == sel_clase]

# -------- Dropdown 2: SUBCLASE --------
opciones_subclase = sorted(df_clase[COL_SUBCLASE].dropna().unique())
sel_subclase = st.selectbox("Subclase", opciones_subclase)

df_subclase = df_clase[df_clase[COL_SUBCLASE] == sel_subclase]

# -------- Dropdown 3: NO. DE PARTE --------
opciones_parte = sorted(df_subclase[COL_PARTE].dropna().unique())
sel_parte = st.selectbox("No. de Parte", opciones_parte)

df_final = df_subclase[df_subclase[COL_PARTE] == sel_parte]

# -------- Mostrar producto seleccionado --------
if len(df_final) == 1:
    fila = df_final.iloc[0]

    st.markdown("### Producto seleccionado")
    st.write(f"**Modelo:** {fila[COL_MODELO]}")
    st.write(f"**Descripción:** {fila[COL_DESC]}")
    st.write(f"**Precio lista:** ${fila[COL_PRECIO]:,.2f}")

    if st.button("Agregar a cotización"):
        precio_lista = float(fila[COL_PRECIO])

        nueva = {
            "SKU": str(fila[COL_PARTE]),
            "DESCRIPCION": str(fila[COL_MODELO]),
            "PRECIO_LISTA": precio_lista,
            "DESC_FAB_PCT": 30.0,
            "MARGEN_PCT": 10.0,
            "COSTO": 0.0,
            "PRECIO_VENTA": 0.0,
            "UTILIDAD_BRUTA": 0.0
        }

        st.session_state.lineas = pd.concat(
            [st.session_state.lineas, pd.DataFrame([nueva])],
            ignore_index=True
        )

        st.session_state.lineas = recalcular_cotizacion(st.session_state.lineas)

# -------- AGREGAR LÍNEA --------
st.subheader("Agregar línea manual / servicio")

with st.form("add_line"):
    sku = st.text_input("SKU")
    desc = st.text_input("Descripción")
    costo = st.number_input("Costo", min_value=0.0)
    precio = st.number_input("Precio de venta", min_value=0.0)

    if st.form_submit_button("Agregar"):
        utilidad = precio - costo
        nueva = pd.DataFrame([{
            "SKU": sku,
            "DESCRIPCION": desc,
            "COSTO": costo,
            "PRECIO_VENTA": precio,
            "UTILIDAD_BRUTA": utilidad
        }])
        st.session_state.lineas = pd.concat(
            [st.session_state.lineas, nueva],
            ignore_index=True
        )

# -------- TABLA EDITABLE --------
st.subheader("Detalle de Cotización")

df_edit = st.data_editor(
    st.session_state.lineas,
    use_container_width=True,
    num_rows="dynamic"
)
df_calc = recalcular_cotizacion(df_edit)

st.session_state.lineas = df_calc
st.dataframe(df_calc, use_container_width=True)

# -------- KPIs --------
total_venta = st.session_state.lineas["PRECIO_VENTA"].sum()
total_costo = st.session_state.lineas["COSTO"].sum()
total_utilidad = st.session_state.lineas["UTILIDAD_BRUTA"].sum()

margen_sobre_venta = (total_utilidad / total_venta) if total_venta > 0 else 0.0
markup_sobre_costo = (total_utilidad / total_costo) if total_costo > 0 else 0.0

c1, c2, c3 = st.columns(3)
c1.metric("Venta Total", f"${total_venta:,.2f}")
c2.metric("Margen sobre Venta", f"{margen_sobre_venta*100:.2f}%")
c3.metric("Markup (sobre costo)", f"{markup_sobre_costo*100:.2f}%")

# -------- GRÁFICAS --------
st.subheader("Aportaciones")

img_precio = grafica_aportacion_precio(df)
img_utilidad = grafica_aportacion_utilidad(df)

st.image(img_precio, caption="Aportación por Precio")
st.image(img_utilidad, caption="Aportación por Utilidad")

# -------- PDF --------
st.subheader("Exportar Cotización")

cliente = st.text_input("Cliente")
contacto = st.text_input("Contacto")
correo = st.text_input("Correo")

if st.button("Generar PDF"):
    pdf = generar_pdf_horizontal(
        df=df,
        cliente=cliente,
        contacto=contacto,
        correo=correo,
        img_precio=img_precio,
        img_utilidad=img_utilidad
    )

    st.download_button(
        "Descargar PDF Horizontal",
        data=pdf,
        file_name="cotizacion.pdf",
        mime="application/pdf"
    )
