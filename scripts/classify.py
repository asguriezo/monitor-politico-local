import sqlite3
import json
import requests
import re

DB_PATH = "../db/database.db"
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3"

# =========================
# 🔌 CONEXIÓN BD
# =========================
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# =========================
# 🤖 LLAMADA A OLLAMA
# =========================
def llamar_ollama(prompt):
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL,
                "prompt": prompt,
                "stream": False
            }
        )

        if response.status_code != 200:
            print("❌ Error HTTP:", response.text)
            return None

        data = response.json()

        if "response" in data:
            return data["response"]
        else:
            print("❌ Respuesta inesperada:", data)
            return None

    except Exception as e:
        print("❌ Error llamando a Ollama:", e)
        return None


# =========================
# 🧠 EXTRAER JSON
# =========================
def extraer_json(texto):
    try:
        return json.loads(texto)
    except:
        pass

    match = re.search(r'\{.*\}', texto, re.DOTALL)
    if not match:
        return None

    json_str = match.group()

    # limpieza básica
    json_str = json_str.replace('\n', ' ')
    json_str = re.sub(r',\s*}', '}', json_str)
    json_str = re.sub(r',\s*]', ']', json_str)
    json_str = re.sub(r'"\w+"\s*:\s*"\w+"\s*:', '', json_str)

    try:
        return json.loads(json_str)
    except:
        return None


# =========================
# 💰 EXTRAER IMPORTES (SIN IA)
# =========================
def extraer_importes(texto):
    importes = []

    # patrón euros típico
    patrones = [
        r'\d{1,3}(?:\.\d{3})*,\d{2}\s?€',  # 1.234,56 €
        r'\d{1,3}(?:\.\d{3})*\s?€',        # 1.234 €
        r'\d+(?:,\d{2})?\s?€'              # 1234 €
    ]

    for patron in patrones:
        encontrados = re.findall(patron, texto)
        importes.extend(encontrados)

    # limpiar duplicados
    importes = list(set(importes))

    return importes

def extraer_empresas(texto):
    empresas = []

    patrones = [
        r'[A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÑ\s]+ S\.L\.',
        r'[A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÑ\s]+ S\.A\.',
        r'[A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÑ\s]+ SL',
        r'[A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÑ\s]+ SA'
    ]

    for patron in patrones:
        encontrados = re.findall(patron, texto)
        empresas.extend(encontrados)

    return list(set(empresas))

def extraer_adjudicaciones(texto):

    adjudicaciones = []

    # dividir en frases (simple)
    frases = re.split(r'\.|\n', texto)

    for frase in frases:

        if any(p in frase.lower() for p in [
            "adjudica", "adjudicado", "adjudicación", "contrato"
        ]):

            # detectar empresa
            empresa_match = re.search(
                r'([A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÑ\s]+ (S\.L\.|S\.A\.|SL|SA))',
                frase
            )

            # detectar importe
            importe_match = re.search(
                r'\d{1,3}(?:\.\d{3})*,\d{2}\s?€|\d+(?:,\d{2})?\s?€',
                frase
            )

            empresa = empresa_match.group() if empresa_match else None
            importe = importe_match.group() if importe_match else None

            if empresa or importe:
                adjudicaciones.append({
                    "empresa": empresa,
                    "importe": importe,
                    "contexto": frase.strip()
                })

    return adjudicaciones


# =========================
# 📄 OBTENER DOCUMENTOS
# =========================
cursor.execute("""
    SELECT id, texto 
    FROM documents 
    WHERE estado='texto_extraido'
""")

docs = cursor.fetchall()

print(f"Procesando {len(docs)} documentos...")

# =========================
# 🔁 PROCESAMIENTO
# =========================
for doc_id, texto in docs:

    print(f"\n📄 Procesando doc {doc_id}")

    # 🔹 extraer importes primero (sin IA)
    importes_detectados = extraer_importes(texto)
    empresas_detectadas = extraer_empresas(texto)
    adjs = extraer_adjudicaciones(texto)

    prompt = f"""
Eres un sistema que extrae información estructurada.

Devuelve SOLO JSON válido.
NO repitas campos.
Si no sabes algo, déjalo vacío.

Texto:
\"\"\"
{texto[:2500]}
\"\"\"

Formato EXACTO:

{{
  "tipo_documento": "acta | decreto | presupuesto | otro",
  "fecha": "YYYY-MM-DD",
  "organismo": "",
  "areas": ["urbanismo", "contratacion", "personal", "subvenciones", "otros"],
  "resumen": "máximo 2 frases",
  "entidades": []
}}
"""

    respuesta = llamar_ollama(prompt)

    if not respuesta:
        print(f"❌ Error en doc {doc_id}")
        continue

    data = extraer_json(respuesta)

    if not data:
        print(f"❌ JSON inválido en doc {doc_id}")
        print("Respuesta:", respuesta[:300])
        continue

    # =========================
    # 📅 FECHA → AÑO
    # =========================
    fecha = data.get("fecha")
    anio = None

    if fecha and len(fecha) >= 4:
        try:
            anio = int(fecha[:4])
        except:
            pass

    # =========================
    # 💾 GUARDAR DOCUMENTO
    # =========================
    cursor.execute("""
        UPDATE documents
        SET tipo=?, fecha=?, anio=?, organismo=?, resumen=?, estado='procesado'
        WHERE id=?
    """, (
        data.get("tipo_documento"),
        fecha,
        anio,
        data.get("organismo"),
        data.get("resumen"),
        doc_id
    ))

    # =========================
    # 🏢 ENTIDADES
    # =========================
    for ent in data.get("entidades", []):
        cursor.execute("""
            INSERT INTO entities (document_id, nombre, tipo)
            VALUES (?, ?, ?)
        """, (doc_id, str(ent), "desconocido"))

    # =========================
    # 🗂️ ÁREAS
    # =========================
    for area in data.get("areas", []):
        cursor.execute("""
            INSERT INTO topics (document_id, area)
            VALUES (?, ?)
        """, (doc_id, str(area)))

    # =========================
    # 💰 GUARDAR IMPORTES (en texto por ahora)
    # =========================
    if importes_detectados:
        #print(f"💰 Importes detectados: {importes_detectados}")
        for imp in importes_detectados:
            cursor.execute("""
                INSERT INTO importes (document_id, valor)
                VALUES (?, ?)
            """, (doc_id, imp))
        
    for emp in empresas_detectadas:
        cursor.execute("""
            INSERT INTO entities (document_id, nombre, tipo)
            VALUES (?, ?, ?)
        """, (doc_id, emp, "empresa"))
    
    for adj in adjs:
        cursor.execute("""
            INSERT INTO adjudicaciones (document_id, empresa, importe, contexto)
            VALUES (?, ?, ?, ?)
        """, (
            doc_id,
            adj["empresa"],
            adj["importe"],
            adj["contexto"]
    ))

# =========================
# ✅ FINALIZAR
# =========================
conn.commit()
conn.close()

print("\n✅ Procesamiento terminado")