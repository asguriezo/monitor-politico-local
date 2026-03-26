CREATE TABLE documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo TEXT,
    tipo TEXT,
    fecha TEXT,
    anio INTEGER,
    organismo TEXT,
    ruta_pdf TEXT,
    texto TEXT,
    resumen TEXT,
    importe_total REAL,
    estado TEXT
);

CREATE TABLE entities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER,
    nombre TEXT,
    tipo TEXT,
    FOREIGN KEY(document_id) REFERENCES documents(id)
);

CREATE TABLE topics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER,
    area TEXT,
    FOREIGN KEY(document_id) REFERENCES documents(id)
);