import streamlit as st
import sqlite3
import pandas as pd
import os

# =========================
# 📁 RUTAS ROBUSTAS
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.abspath(os.path.join(BASE_DIR, "../db/database.db"))
SCHEMA_PATH = os.path.abspath(os.path.join(BASE_DIR, "../db/schema.sql"))

# =========================
# 🗄️ CREAR BD SI NO EXISTE
# =========================
def init_db():
    if not os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        if os.path.exists(SCHEMA_PATH):
            with open(SCHEMA_PATH, "r") as f:
                conn.executescript(f.read())
        conn.commit()
        conn.close()

init_db()

# =========================
# 🔌 CONEXIÓN
# =========================
conn = sqlite3.connect(DB_PATH, check_same_thread=False)

# =========================
# 🧪 DEBUG (opcional)
# =========================
with st.expander("🔍 Debug"):
    st.write("Directorio actual:", os.getcwd())
    st.write("DB_PATH:", DB_PATH)
    st.write("Existe DB:", os.path.exists(DB_PATH))

# =========================
# 🖥️ UI
# =========================
st.title("📊 Observatorio Municipal")

# =========================
# 🔎 FILTROS
# =========================
query = st.text_input("Buscar en texto")

tipo_filter = st.selectbox(
    "Tipo de documento",
    ["Todos", "acta", "decreto", "presupuesto"]
)

# =========================
# 📊 CARGAR DATOS
# =========================
df = pd.read_sql_query("SELECT * FROM documents", conn)

# =========================
# 🔍 FILTRADO
# =========================
if query:
    df = df[df["texto"].fillna("").str.contains(query, case=False)]

if tipo_filter != "Todos":
    df = df[df["tipo"] == tipo_filter]

# =========================
# 📋 TABLA
# =========================
st.subheader("📄 Documentos")
st.dataframe(df[["id", "titulo", "tipo", "fecha", "resumen"]])

# =========================
# 📄 DETALLE DOCUMENTO
# =========================
doc_id = st.number_input("Ver documento (ID)", min_value=0, step=1)

if doc_id:
    doc = pd.read_sql_query(
        f"SELECT * FROM documents WHERE id={doc_id}", conn
    )

    if not doc.empty:
        d = doc.iloc[0]

        st.markdown("## 📄 Detalle")
        st.write("**Título:**", d["titulo"])
        st.write("**Tipo:**", d["tipo"])
        st.write("**Fecha:**", d["fecha"])
        st.write("**Organismo:**", d["organismo"])

        st.markdown("### 🧠 Resumen")
        st.write(d["resumen"])

        st.markdown("### 📜 Texto")
        st.text(d["texto"][:2000])  # limitamos para no romper la app
    else:
        st.warning("Documento no encontrado")

# =========================
# 📊 DASHBOARD BÁSICO
# =========================
st.subheader("📈 Estadísticas")

if not df.empty:

    # documentos por tipo
    tipo_counts = df["tipo"].value_counts()
    st.bar_chart(tipo_counts)

    # documentos por año
    if "anio" in df.columns:
        anio_counts = df["anio"].value_counts().sort_index()
        st.line_chart(anio_counts)

else:
    st.info("No hay datos aún")
