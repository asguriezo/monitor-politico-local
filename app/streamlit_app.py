import streamlit as st
import sqlite3
import pandas as pd
import os

# =========================
# 📁 RUTAS
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.abspath(os.path.join(BASE_DIR, "../db/database.db"))
SCHEMA_PATH = os.path.abspath(os.path.join(BASE_DIR, "../db/schema.sql"))

# =========================
# 🗄️ INIT DB
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
# 🧪 DEBUG
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
    ["Todos", "acta", "decreto", "presupuesto", "otro"]
)

# =========================
# 📊 CARGAR DOCUMENTOS
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
        st.text(d["texto"][:2000])
    else:
        st.warning("Documento no encontrado")

# =========================
# 📊 DASHBOARD GENERAL
# =========================
st.subheader("📈 Estadísticas")

if not df.empty:

    tipo_counts = df["tipo"].value_counts()
    st.bar_chart(tipo_counts)

    if "anio" in df.columns:
        anio_counts = df["anio"].value_counts().sort_index()
        st.line_chart(anio_counts)

else:
    st.info("No hay datos aún")

# =========================
# 💰 DASHBOARD ECONÓMICO
# =========================
st.subheader("💰 Análisis económico")

try:
    importes_df = pd.read_sql_query("""
        SELECT d.id, d.titulo, i.valor
        FROM importes i
        JOIN documents d ON d.id = i.document_id
    """, conn)

    if not importes_df.empty:

        # limpiar valores
        importes_df["valor_num"] = (
            importes_df["valor"]
            .str.replace("€", "", regex=False)
            .str.replace(".", "", regex=False)
            .str.replace(",", ".", regex=False)
            .astype(float)
        )

        # total €
        total = importes_df["valor_num"].sum()
        st.metric("💰 Total detectado (€)", f"{total:,.2f}")

        # top documentos por importe
        st.markdown("### 📊 Top documentos por importe")

        por_doc = (
            importes_df
            .groupby("titulo")["valor_num"]
            .sum()
            .sort_values(ascending=False)
        )

        st.bar_chart(por_doc.head(10))

    else:
        st.info("No hay importes detectados aún")

except Exception as e:
    st.warning("⚠️ Tabla importes no disponible o error en datos")

# =========================
# 🏢 EMPRESAS
# =========================
st.subheader("🏢 Empresas")

try:
    empresas_df = pd.read_sql_query("""
        SELECT nombre, COUNT(*) as total
        FROM entities
        WHERE tipo='empresa'
        GROUP BY nombre
        ORDER BY total DESC
    """, conn)

    if not empresas_df.empty:
        st.bar_chart(empresas_df.set_index("nombre"))
    else:
        st.info("No hay empresas detectadas")

except Exception as e:
    st.warning("⚠️ Error cargando empresas")
    
st.subheader("💰🏢 Dinero por empresa")

try:
    cruce_df = pd.read_sql_query("""
        SELECT e.nombre as empresa, i.valor
        FROM importes i
        JOIN entities e ON e.document_id = i.document_id
        WHERE e.tipo = 'empresa'
    """, conn)

    if not cruce_df.empty:

        # limpiar importes
        cruce_df["valor_num"] = (
            cruce_df["valor"]
            .str.replace("€", "", regex=False)
            .str.replace(".", "", regex=False)
            .str.replace(",", ".", regex=False)
            .astype(float)
        )

        # agrupar por empresa
        por_empresa = (
            cruce_df
            .groupby("empresa")["valor_num"]
            .sum()
            .sort_values(ascending=False)
        )

        # 💰 TOP empresas
        st.markdown("### 🏆 Empresas con más importe")

        st.bar_chart(por_empresa.head(10))

        # tabla detalle
        st.markdown("### 📋 Detalle")

        st.dataframe(
            por_empresa.reset_index().rename(columns={"valor_num": "total €"})
        )

    else:
        st.info("No hay datos suficientes para cruce")

except Exception as e:
    st.warning(f"⚠️ Error en cruce: {e}")
    

st.subheader("📜 Adjudicaciones detectadas")

try:
    adj_df = pd.read_sql_query("""
        SELECT d.titulo, a.empresa, a.importe, a.contexto
        FROM adjudicaciones a
        JOIN documents d ON d.id = a.document_id
    """, conn)

    if not adj_df.empty:
        st.dataframe(adj_df)
    else:
        st.info("No hay adjudicaciones detectadas")

except Exception as e:
    st.warning("Error cargando adjudicaciones")


st.subheader("⚠️ Alertas")

try:
    alerts_df = pd.read_sql_query("""
        SELECT tipo, descripcion, fecha
        FROM alerts
        ORDER BY fecha DESC
    """, conn)

    if not alerts_df.empty:
        st.dataframe(alerts_df)
    else:
        st.info("No hay alertas generadas")

except:
    st.warning("Error cargando alertas")