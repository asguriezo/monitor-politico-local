import sqlite3
import pandas as pd

conn = sqlite3.connect("../db/database.db")
cursor = conn.cursor()

print("Calculando scores...")

# limpiar scores previos
cursor.execute("DELETE FROM document_scores")

# =========================
# 📊 BASE DOCUMENTOS
# =========================
docs = pd.read_sql_query("SELECT id FROM documents", conn)

# =========================
# 💰 IMPORTES
# =========================
df_imp = pd.read_sql_query("SELECT document_id, valor FROM importes", conn)

def limpiar(valor):
    try:
        return float(
            valor.replace("€", "")
                 .replace(".", "")
                 .replace(",", ".")
        )
    except:
        return 0

df_imp["valor_num"] = df_imp["valor"].apply(limpiar)

# umbral dinámico
umbral = df_imp["valor_num"].quantile(0.9) if not df_imp.empty else 0

# =========================
# 🏢 EMPRESAS RECURRENTES
# =========================
df_emp = pd.read_sql_query("""
    SELECT nombre, COUNT(*) as total
    FROM entities
    WHERE tipo='empresa'
    GROUP BY nombre
""", conn)

empresas_recurrentes = set(df_emp[df_emp["total"] >= 3]["nombre"])

# =========================
# 📜 ADJUDICACIONES
# =========================
df_adj = pd.read_sql_query("""
    SELECT document_id, empresa, importe
    FROM adjudicaciones
""", conn)

# =========================
# 🔁 SCORING
# =========================
for _, doc in docs.iterrows():

    doc_id = int(doc["id"])
    score = 0

    # 💰 importe alto
    imp_doc = df_imp[df_imp["document_id"] == doc_id]
    if not imp_doc.empty and any(imp_doc["valor_num"] > umbral):
        score += 3

    # 📜 adjudicaciones
    adj_doc = df_adj[df_adj["document_id"] == doc_id]

    if not adj_doc.empty:
        score += 2

        # ❌ sin importe
        if any(adj_doc["importe"].isnull()):
            score += 3

    # 🏢 empresa recurrente
    for _, row in adj_doc.iterrows():
        if row["empresa"] in empresas_recurrentes:
            score += 2

    # =========================
    # 🎯 NIVEL
    # =========================
    if score >= 6:
        nivel = "alto"
    elif score >= 3:
        nivel = "medio"
    else:
        nivel = "bajo"

    cursor.execute("""
        INSERT INTO document_scores (document_id, score, nivel)
        VALUES (?, ?, ?)
    """, (doc_id, score, nivel))

conn.commit()
conn.close()

print("Scores generados")