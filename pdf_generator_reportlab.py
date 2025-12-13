from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Image, PageBreak
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import io

def generar_pdf_horizontal(df, cliente, contacto, correo, img_precio, img_utilidad):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),
        leftMargin=30,
        rightMargin=30,
        topMargin=30,
        bottomMargin=30
    )

    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("COTIZACIÓN", styles["Title"]))
    story.append(Paragraph(f"Cliente: {cliente}", styles["Normal"]))
    story.append(Paragraph(f"Contacto: {contacto}", styles["Normal"]))
    story.append(Paragraph(f"Correo: {correo}", styles["Normal"]))

    data = [df.columns.tolist()] + df.values.tolist()
    tabla = Table(data, repeatRows=1)
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.black),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("GRID", (0,0), (-1,-1), 0.25, colors.grey),
        ("FONTSIZE", (0,0), (-1,-1), 8),
    ]))

    story.append(tabla)
    story.append(PageBreak())

    story.append(Paragraph("Gráficas de Aportación", styles["Heading1"]))
    story.append(Image(img_precio, width=500, height=250))
    story.append(Image(img_utilidad, width=500, height=250))

    doc.build(story)
    buffer.seek(0)
    return buffer
