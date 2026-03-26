import os
import sqlite3

DB_PATH = "../db/database.db"
PDF_FOLDER = "../data/raw_pdfs"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

for file in os.listdir(PDF_FOLDER):
    if file.endswith(".pdf"):
        ruta = os.path.join(PDF_FOLDER, file)

        cursor.execute("""
            INSERT INTO documents (titulo, ruta_pdf, estado)
            VALUES (?, ?, ?)
        """, (file, ruta, "pendiente"))

conn.commit()
conn.close()