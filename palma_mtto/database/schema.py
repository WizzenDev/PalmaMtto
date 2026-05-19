from .connection import get_connection

def create_tables():
    conn = get_connection()
    cur = conn.cursor()
    cur.executescript('''
    CREATE TABLE IF NOT EXISTS mensajes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha TEXT,
        hora TEXT,
        remitente TEXT,
        texto TEXT,
        adjuntos TEXT,
        media_omitida INTEGER,
        estado_proceso TEXT,
        id_lote INTEGER,
        equipo TEXT,
        tipo_mensaje TEXT,
        editado_manual INTEGER,
        fecha_proceso TEXT
    );
    CREATE TABLE IF NOT EXISTS lotes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        numero_lote INTEGER,
        id_primer_mensaje INTEGER,
        id_ultimo_mensaje INTEGER,
        cantidad_mensajes INTEGER,
        estado TEXT,
        proveedor_ia TEXT,
        tokens_usados INTEGER,
        fecha_proceso TEXT,
        error_detalle TEXT
    );
    CREATE TABLE IF NOT EXISTS equipos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT UNIQUE,
        descripcion TEXT,
        activo INTEGER,
        origen TEXT,
        fecha_creacion TEXT
    );
    CREATE TABLE IF NOT EXISTS configuracion (
        clave TEXT PRIMARY KEY,
        valor TEXT
    );
    ''')
    conn.commit()
