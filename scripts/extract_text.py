import fitz  # PyMuPDF
import sqlite3

DB_PATH = "../db/database.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("SELECT id, ruta_pdf FROM documents WHERE estado='pendiente'")
docs = cursor.fetchall()

for doc_id, ruta in docs:
    try:
        pdf = fitz.open(ruta)
        text = ""

        for page in pdf:
            text += page.get_text()

        cursor.execute("""
            UPDATE documents
            SET texto=?, estado='texto_extraido'
            WHERE id=?
        """, (text, doc_id))

    except Exception as e:
        print(f"Error en {ruta}: {e}")

conn.commit()
conn.close()