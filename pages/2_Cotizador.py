import streamlit as st
import pandas as pd
from graph_utils import grafica_aportacion_precio, grafica_aportacion_utilidad
from pdf_generator_reportlab import generar_pdf_horizontal

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
            "COSTO",
            "PRECIO_VENTA",
            "UTILIDAD_BRUTA"
        ]
    )

# -------- BUSCADOR --------
query = st.text_input("Buscar por SKU o DESCRIPCIÓN")

if query:
    coincidencias = catalogo[
        catalogo.astype(str).apply(
            lambda row: row.str.contains(query, case=False, na=False).any(),
            axis=1
        )
    ]
    st.dataframe(coincidencias.head(10), use_container_width=True)

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

df = st.data_editor(
    st.session_state.lineas,
    use_container_width=True,
    num_rows="dynamic"
)

# Recalcular utilidad por edición
df["UTILIDAD_BRUTA"] = df["PRECIO_VENTA"] - df["COSTO"]
st.session_state.lineas = df

# -------- KPIs --------
total_venta = df["PRECIO_VENTA"].sum()
total_costo = df["COSTO"].sum()
total_utilidad = df["UTILIDAD_BRUTA"].sum()

margen_venta = total_utilidad / total_venta if total_venta > 0 else 0
margen_costo = total_utilidad / total_costo if total_costo > 0 else 0

c1, c2, c3 = st.columns(3)
c1.metric("Venta Total", f"${total_venta:,.2f}")
c2.metric("Margen sobre Venta", f"{margen_venta*100:.2f}%")
c3.metric("Markup (sobre costo)", f"{margen_costo*100:.2f}%")

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
