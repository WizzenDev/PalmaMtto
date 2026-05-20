"""
database/schema.py
------------------
Creación de tablas, índices y datos de configuración predeterminados.

Se usa CREATE TABLE IF NOT EXISTS para que sea seguro llamar inicializar()
en cada arranque de la aplicación sin destruir datos existentes.

Decisión de diseño: la tabla `lotes` se crea antes que `mensajes` para que
la FK de mensajes.id_lote pueda resolverse. SQLite con PRAGMA foreign_keys=ON
valida esto en tiempo de escritura, no de creación, pero mantenerlo en orden
es buena práctica.
"""

import sqlite3

from database.connection import db


# ---------------------------------------------------------------------------
# SQL de creación de tablas
# ---------------------------------------------------------------------------

_SQL_TABLA_LOTES = """
CREATE TABLE IF NOT EXISTS lotes (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    numero_lote         INTEGER NOT NULL,
    id_primer_mensaje   INTEGER,
    id_ultimo_mensaje   INTEGER,
    cantidad_mensajes   INTEGER DEFAULT 0,
    estado              TEXT    DEFAULT 'pendiente',
    proveedor_ia        TEXT,
    tokens_usados       INTEGER,
    fecha_proceso       TEXT,
    error_detalle       TEXT
)
"""

_SQL_TABLA_MENSAJES = """
CREATE TABLE IF NOT EXISTS mensajes (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha           TEXT    NOT NULL,
    hora            TEXT    NOT NULL,
    remitente       TEXT    NOT NULL,
    texto           TEXT,
    adjuntos        TEXT    DEFAULT '[]',
    media_omitida   INTEGER DEFAULT 0,
    estado_proceso  TEXT    DEFAULT 'sin_procesar',
    id_lote         INTEGER REFERENCES lotes(id) ON DELETE SET NULL,
    equipo          TEXT,
    tipo_mensaje    TEXT,
    editado_manual  INTEGER DEFAULT 0,
    fecha_proceso   TEXT
)
"""

_SQL_TABLA_EQUIPOS = """
CREATE TABLE IF NOT EXISTS equipos (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre          TEXT UNIQUE NOT NULL,
    descripcion     TEXT,
    activo          INTEGER DEFAULT 1,
    origen          TEXT    DEFAULT 'manual',
    fecha_creacion  TEXT    DEFAULT (datetime('now', 'localtime'))
)
"""

_SQL_TABLA_CONFIGURACION = """
CREATE TABLE IF NOT EXISTS configuracion (
    clave   TEXT PRIMARY KEY,
    valor   TEXT
)
"""

# ---------------------------------------------------------------------------
# SQL de índices
# ---------------------------------------------------------------------------

_INDICES: list[str] = [
    "CREATE INDEX IF NOT EXISTS idx_mensajes_fecha      ON mensajes(fecha)",
    "CREATE INDEX IF NOT EXISTS idx_mensajes_remitente  ON mensajes(remitente)",
    "CREATE INDEX IF NOT EXISTS idx_mensajes_estado     ON mensajes(estado_proceso)",
    "CREATE INDEX IF NOT EXISTS idx_mensajes_equipo     ON mensajes(equipo)",
    "CREATE INDEX IF NOT EXISTS idx_mensajes_tipo       ON mensajes(tipo_mensaje)",
    "CREATE INDEX IF NOT EXISTS idx_mensajes_lote       ON mensajes(id_lote)",
    "CREATE INDEX IF NOT EXISTS idx_equipos_activo      ON equipos(activo)",
]

# ---------------------------------------------------------------------------
# Configuración predeterminada
# ---------------------------------------------------------------------------

_PROMPT_BASE_DEFAULT = (
    "Eres un asistente especializado en mantenimiento industrial de plantas "
    "extractoras de aceite de palma. Analiza los mensajes de WhatsApp del grupo "
    "de mantenimiento y clasifica cada uno según el equipo involucrado y el tipo "
    "de mensaje.\n\n"
    "Instrucciones:\n"
    "- Identifica el equipo usando exactamente los nombres de la lista proporcionada.\n"
    "- Si el equipo no está en la lista pero lo identificas, usa el nombre del mensaje.\n"
    "- Si no aplica ningún equipo, usa null.\n"
    "- Sé preciso con el tipo de mensaje según las definiciones dadas."
)

_CONFIG_DEFAULT: list[tuple[str, str]] = [
    ("proveedor_ia",               "openai"),
    ("api_key_openai",             ""),
    ("api_key_anthropic",          ""),
    ("api_key_gemini",             ""),
    ("directorio_multimedia",      ""),
    ("tamano_lote",                "50"),
    ("pausa_entre_lotes",          "1"),
    ("agregar_equipos_automatico", "1"),
    ("confirmar_procesar_todos",   "1"),
    ("tema",                       "claro"),
    ("tamano_fuente_tabla",        "11"),
    ("modelo_openai",              "gpt-4o-mini"),
    ("modelo_anthropic",           "claude-sonnet-4-20250514"),
    ("modelo_gemini",              "gemini-2.0-flash"),
    ("modelo_ollama",              "llama3"),
    ("url_ollama",                 "http://localhost:11434"),
    ("prompt_base",                _PROMPT_BASE_DEFAULT),
]


# ---------------------------------------------------------------------------
# Función pública
# ---------------------------------------------------------------------------

def inicializar() -> None:
    """
    Crea todas las tablas, índices y datos predeterminados si no existen.

    Debe llamarse una vez al arrancar la aplicación, después de db.connect().
    Es idempotente: se puede llamar múltiples veces sin efectos secundarios.
    """
    conn = db.get_connection()
    cursor = conn.cursor()

    # Tablas (lotes primero por la FK de mensajes)
    for sql in [
        _SQL_TABLA_LOTES,
        _SQL_TABLA_MENSAJES,
        _SQL_TABLA_EQUIPOS,
        _SQL_TABLA_CONFIGURACION,
    ]:
        cursor.execute(sql)

    # Índices
    for sql in _INDICES:
        cursor.execute(sql)

    # Configuración predeterminada (INSERT OR IGNORE respeta valores existentes)
    cursor.executemany(
        "INSERT OR IGNORE INTO configuracion (clave, valor) VALUES (?, ?)",
        _CONFIG_DEFAULT,
    )

    conn.commit()


def obtener_version_esquema() -> int:
    """
    Retorna el número de versión del esquema almacenado en configuración.
    Útil para el módulo de migraciones futuras.
    """
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT valor FROM configuracion WHERE clave = 'version_esquema'"
    )
    row = cursor.fetchone()
    return int(row["valor"]) if row else 0


def establecer_version_esquema(version: int) -> None:
    """Guarda el número de versión del esquema en la tabla configuracion."""
    conn = db.get_connection()
    conn.execute(
        "INSERT OR REPLACE INTO configuracion (clave, valor) VALUES ('version_esquema', ?)",
        (str(version),),
    )
    conn.commit()


# ---------------------------------------------------------------------------
# Siguiente archivo a construir: database/models.py
# ---------------------------------------------------------------------------
