import matplotlib.pyplot as plt
import io

def grafica_aportacion_precio(df):
    fig, ax = plt.subplots(figsize=(6, 3))
    ax.bar(df["DESCRIPCION"], df["PRECIO_VENTA"])
    ax.set_title("Aportación por Precio")
    ax.tick_params(axis="x", rotation=45)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    buf.seek(0)
    return buf

def grafica_aportacion_utilidad(df):
    fig, ax = plt.subplots(figsize=(6, 3))
    ax.bar(df["DESCRIPCION"], df["UTILIDAD_BRUTA"])
    ax.set_title("Aportación por Utilidad Bruta")
    ax.tick_params(axis="x", rotation=45)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    buf.seek(0)
    return buf
