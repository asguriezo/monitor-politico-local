import sqlite3
import pandas as pd
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

DB_PATH = "../db/database.db"

conn = sqlite3.connect(DB_PATH)

# =========================
# 📊 CARGAR DATOS
# =========================
df = pd.read_sql_query("""
    SELECT d.titulo, d.fecha, s.score, s.nivel, s.explicacion
    FROM document_scores s
    JOIN documents d ON d.id = s.document_id
    WHERE s.nivel = 'alto'
    ORDER BY s.score DESC
""", conn)

conn.close()

# =========================
# 📄 CREAR PDF
# =========================
doc = SimpleDocTemplate("../informes/informe_riesgo.pdf")

styles = getSampleStyleSheet()
contenido = []

# título
contenido.append(Paragraph("Informe de Riesgo Municipal", styles["Title"]))
contenido.append(Spacer(1, 12))

# =========================
# 📄 DOCUMENTOS
# =========================
for _, row in df.iterrows():

    texto = f"""
    <b>{row['titulo']}</b><br/>
    Fecha: {row['fecha']}<br/>
    Nivel: {row['nivel']} | Score: {row['score']}<br/>
    Motivos: {row['explicacion']}<br/>
    """

    contenido.append(Paragraph(texto, styles["Normal"]))
    contenido.append(Spacer(1, 12))

# =========================
# 💾 GUARDAR
# =========================
doc.build(contenido)

print("✅ PDF generado en /informes/informe_riesgo.pdf")