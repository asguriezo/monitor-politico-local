import sqlite3
import pandas as pd

DB_PATH = "../db/database.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print("Calculando scores...")

# =========================
# 🧹 LIMPIAR SCORES PREVIOS
# =========================
cursor.execute("DELETE FROM document_scores")

# =========================
# 📊 DOCUMENTOS
# =========================
docs = pd.read_sql_query("SELECT id FROM documents", conn)

# =========================
# 💰 IMPORTES
# =========================
df_imp = pd.read_sql_query("""
    SELECT document_id, valor
    FROM importes
""", conn)

def limpiar(valor):
    try:
        return float(
            valor.replace("€", "")
                 .replace(".", "")
                 .replace(",", ".")
        )
    except:
        return 0

if not df_imp.empty:
    df_imp["valor_num"] = df_imp["valor"].apply(limpiar)
    umbral = df_imp["valor_num"].quantile(0.9)
else:
    umbral = 0

# =========================
# 🏢 EMPRESAS RECURRENTES
# =========================
df_emp = pd.read_sql_query("""
    SELECT nombre, COUNT(*) as total
    FROM entities
    WHERE tipo='empresa'
    GROUP BY nombre
""", conn)

empresas_recurrentes = set(
    df_emp[df_emp["total"] >= 3]["nombre"]
)

# =========================
# 📜 ADJUDICACIONES
# =========================
df_adj = pd.read_sql_query("""
    SELECT document_id, empresa, importe
    FROM adjudicaciones
""", conn)

# =========================
# 🔁 SCORING POR DOCUMENTO
# =========================
for _, doc in docs.iterrows():

    doc_id = int(doc["id"])
    score = 0
    motivos = []

    # =========================
    # 💰 IMPORTE ALTO
    # =========================
    imp_doc = df_imp[df_imp["document_id"] == doc_id]

    if not imp_doc.empty and any(imp_doc["valor_num"] > umbral):
        score += 3
        motivos.append("Importe elevado detectado")

    # =========================
    # 📜 ADJUDICACIONES
    # =========================
    adj_doc = df_adj[df_adj["document_id"] == doc_id]

    if not adj_doc.empty:
        score += 2
        motivos.append("Contiene adjudicación")

        # ❌ adjudicación sin importe
        if any(adj_doc["importe"].isnull()):
            score += 3
            motivos.append("Adjudicación sin importe")

        # 🏢 empresa recurrente
        for _, row in adj_doc.iterrows():
            if row["empresa"] and row["empresa"] in empresas_recurrentes:
                score += 2
                motivos.append(f"Empresa recurrente: {row['empresa']}")

    # =========================
    # 🎯 NIVEL DE RIESGO
    # =========================
    if score >= 6:
        nivel = "alto"
    elif score >= 3:
        nivel = "medio"
    else:
        nivel = "bajo"

    # =========================
    # 🧠 EXPLICACIÓN
    # =========================
    if motivos:
        # eliminar duplicados manteniendo orden
        motivos_unicos = list(dict.fromkeys(motivos))
        explicacion = " | ".join(motivos_unicos)
    else:
        explicacion = "Sin incidencias relevantes"

    # =========================
    # 💾 GUARDAR
    # =========================
    cursor.execute("""
        INSERT INTO document_scores (document_id, score, nivel, explicacion)
        VALUES (?, ?, ?, ?)
    """, (doc_id, score, nivel, explicacion))

# =========================
# ✅ FINALIZAR
# =========================
conn.commit()
conn.close()

print("✅ Scores generados correctamente")