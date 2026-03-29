import sqlite3
import pandas as pd

conn = sqlite3.connect("../db/database.db")
cursor = conn.cursor()

print("Generando alertas...")

# limpiar alertas previas (opcional)
cursor.execute("DELETE FROM alerts")

# =========================
# 🏢 EMPRESAS FRECUENTES
# =========================
df_emp = pd.read_sql_query("""
    SELECT nombre, COUNT(*) as total
    FROM entities
    WHERE tipo='empresa'
    GROUP BY nombre
""", conn)

for _, row in df_emp.iterrows():
    if row["total"] >= 3:
        cursor.execute("""
            INSERT INTO alerts (tipo, descripcion)
            VALUES (?, ?)
        """, (
            "empresa_recurrente",
            f"La empresa {row['nombre']} aparece {row['total']} veces"
        ))

# =========================
# 💰 IMPORTES ALTOS
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

df_imp["valor_num"] = df_imp["valor"].apply(limpiar)

for _, row in df_imp.iterrows():
    if row["valor_num"] > 50000:  # umbral ajustable
        cursor.execute("""
            INSERT INTO alerts (tipo, descripcion, document_id)
            VALUES (?, ?, ?)
        """, (
            "importe_alto",
            f"Importe elevado detectado: {row['valor']}",
            int(row["document_id"])
        ))

# =========================
# 📜 ADJUDICACIONES SIN IMPORTE
# =========================
df_adj = pd.read_sql_query("""
    SELECT document_id, empresa, importe
    FROM adjudicaciones
""", conn)

for _, row in df_adj.iterrows():
    if row["empresa"] and not row["importe"]:
        cursor.execute("""
            INSERT INTO alerts (tipo, descripcion, document_id)
            VALUES (?, ?, ?)
        """, (
            "adjudicacion_sin_importe",
            f"Adjudicación a {row['empresa']} sin importe detectado",
            int(row["document_id"])
        ))

# =========================
# 🔁 POSIBLES REPETICIONES
# =========================
df_rep = pd.read_sql_query("""
    SELECT empresa, COUNT(*) as total
    FROM adjudicaciones
    WHERE empresa IS NOT NULL
    GROUP BY empresa
""", conn)

for _, row in df_rep.iterrows():
    if row["total"] >= 3:
        cursor.execute("""
            INSERT INTO alerts (tipo, descripcion)
            VALUES (?, ?)
        """, (
            "contratos_repetidos",
            f"La empresa {row['empresa']} tiene múltiples adjudicaciones ({row['total']})"
        ))

conn.commit()
conn.close()

print("Alertas generadas")