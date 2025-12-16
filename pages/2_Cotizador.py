import streamlit as st
import pandas as pd
from graph_utils import (
    grafica_aportacion_precio, 
    grafica_aportacion_utilidad,
    grafica_pie_precio,
    grafica_pie_utilidad
)
from pdf_generator_reportlab import generar_pdf_horizontal
import numpy as np

def recalcular_cotizacion(df: pd.DataFrame, df_anterior: pd.DataFrame = None) -> pd.DataFrame:
    df = df.copy()

    # --- Asegurar columnas base ---
    columnas_base = {
        "PRECIO_LISTA": 0.0,
        "DESC_FAB_PCT": 0.0,
        "MARGEN_PCT": 0.0,
        "COSTO": 0.0,
        "PRECIO_VENTA": 0.0,
        "UTILIDAD_BRUTA": 0.0,
    }

    for col, default in columnas_base.items():
        if col not in df.columns:
            df[col] = default

    # --- Forzar numéricos ---
    for col in columnas_base.keys():
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

    # --- Detectar qué cambió para calcular correctamente ---
    for idx in df.index:
        # Siempre recalcular COSTO desde PRECIO_LISTA y DESC_FAB_PCT
        df.loc[idx, "COSTO"] = df.loc[idx, "PRECIO_LISTA"] * (1.0 - df.loc[idx, "DESC_FAB_PCT"] / 100.0)
        
        # Si hay df_anterior, detectar qué se modificó
        if df_anterior is not None and idx in df_anterior.index:
            precio_venta_cambio = df.loc[idx, "PRECIO_VENTA"] != df_anterior.loc[idx, "PRECIO_VENTA"]
            margen_cambio = df.loc[idx, "MARGEN_PCT"] != df_anterior.loc[idx, "MARGEN_PCT"]
            
            # Si se modificó PRECIO_VENTA directamente, recalcular MARGEN_PCT
            if precio_venta_cambio and not margen_cambio:
                precio = df.loc[idx, "PRECIO_VENTA"]
                costo = df.loc[idx, "COSTO"]
                if precio > 0:
                    df.loc[idx, "MARGEN_PCT"] = ((precio - costo) / precio) * 100
            # Si se modificó MARGEN_PCT, recalcular PRECIO_VENTA
            else:
                margen = df.loc[idx, "MARGEN_PCT"]
                costo = df.loc[idx, "COSTO"]
                denom = 1.0 - (margen / 100.0)
                if denom != 0:
                    df.loc[idx, "PRECIO_VENTA"] = costo / denom
                else:
                    df.loc[idx, "PRECIO_VENTA"] = 0.0
        else:
            # Línea nueva o sin comparación: calcular desde margen
            margen = df.loc[idx, "MARGEN_PCT"]
            costo = df.loc[idx, "COSTO"]
            denom = 1.0 - (margen / 100.0)
            if denom != 0:
                df.loc[idx, "PRECIO_VENTA"] = costo / denom
            else:
                df.loc[idx, "PRECIO_VENTA"] = 0.0
        
        # Siempre recalcular UTILIDAD_BRUTA
        df.loc[idx, "UTILIDAD_BRUTA"] = df.loc[idx, "PRECIO_VENTA"] - df.loc[idx, "COSTO"]

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
    num_rows="dynamic",
    key="editor_lineas"
)

# Recalcular solo si hubo cambios
if not df_edit.equals(st.session_state.lineas):
    df_calc = recalcular_cotizacion(df_edit, st.session_state.lineas)
    st.session_state.lineas = df_calc
    st.rerun()

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

img_precio = grafica_aportacion_precio(st.session_state.lineas)
img_utilidad = grafica_aportacion_utilidad(st.session_state.lineas)
img_pie_precio = grafica_pie_precio(st.session_state.lineas)
img_pie_utilidad = grafica_pie_utilidad(st.session_state.lineas)

col1, col2 = st.columns(2)
with col1:
    st.image(img_precio, caption="Aportación por Precio")
    st.image(img_pie_precio, caption="Distribución por Precio")
with col2:
    st.image(img_utilidad, caption="Aportación por Utilidad")
    st.image(img_pie_utilidad, caption="Distribución por Utilidad")

# -------- PDF --------
st.subheader("Exportar Cotización")

cliente = st.text_input("Cliente")
contacto = st.text_input("Contacto")
correo = st.text_input("Correo")

if st.button("Generar PDF"):
    pdf = generar_pdf_horizontal(
        df=st.session_state.lineas,
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
