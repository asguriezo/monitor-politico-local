import streamlit as st
import sqlite3
import pandas as pd

conn = sqlite3.connect("../db/database.db")

st.title("Observatorio Municipal")

query = st.text_input("Buscar")

df = pd.read_sql_query("SELECT * FROM documents", conn)

if query:
    df = df[df["texto"].str.contains(query, case=False, na=False)]

st.dataframe(df[["id", "titulo", "tipo", "fecha", "resumen"]])