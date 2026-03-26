import sqlite3
import json
import requests

DB_PATH = "../db/database.db"
OLLAMA_URL = "http://localhost:11434/api/generate"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("SELECT id, texto FROM documents WHERE estado='texto_extraido'")
docs = cursor.fetchall()

def llamar_ollama(prompt):  
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": "mistral",
            "prompt": prompt,
            "stream": False
        }
    )
    return response.json()["response"]

for doc_id, texto in docs:

    prompt = f"""
Eres un sistema experto en análisis de documentos municipales.

Devuelve SOLO JSON válido (sin texto adicional).

Texto:
\"\"\"
{texto[:3000]}
\"\"\"

Formato:
{{
  "tipo_documento": "",
  "fecha": "",
  "organismo": "",
  "areas": [],
  "resumen": "",
  "importes": [],
  "entidades": []
}}
"""

    try:
        respuesta = llamar_ollama(prompt)

        # intentar parsear JSON
        data = json.loads(respuesta)

    except Exception as e:
        print(f"Error JSON en doc {doc_id}: {e}")
        continue

    cursor.execute("""
        UPDATE documents
        SET tipo=?, fecha=?, anio=?, organismo=?, resumen=?, estado='procesado'
        WHERE id=?
    """, (
        data.get("tipo_documento"),
        data.get("fecha"),
        int(data.get("fecha", "0")[:4]) if data.get("fecha") else None,
        data.get("organismo"),
        data.get("resumen"),
        doc_id
    ))

    # entidades
    for ent in data.get("entidades", []):
        cursor.execute("""
            INSERT INTO entities (document_id, nombre, tipo)
            VALUES (?, ?, ?)
        """, (doc_id, ent, "desconocido"))

    # áreas
    for area in data.get("areas", []):
        cursor.execute("""
            INSERT INTO topics (document_id, area)
            VALUES (?, ?)
        """, (doc_id, area))

conn.commit()
conn.close()