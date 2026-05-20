"""
database/repo_config.py
-----------------------
Repositorio para la tabla configuracion.
"""

from database.connection import db


def get_str(clave: str, default: str = "") -> str:
    conn = db.get_connection()
    cur = conn.cursor()
    cur.execute("SELECT valor FROM configuracion WHERE clave = ?", (clave,))
    row = cur.fetchone()
    return row[0] if row and row[0] is not None else default


def get_int(clave: str, default: int = 0) -> int:
    try:
        return int(get_str(clave, str(default)))
    except ValueError:
        return default


def get_bool(clave: str, default: bool = False) -> bool:
    val = get_str(clave, "1" if default else "0").lower()
    if val in ("1", "true", "yes"):
        return True
    if val in ("0", "false", "no"):
        return False
    return default


def set_value(clave: str, valor: str) -> None:
    conn = db.get_connection()
    conn.execute(
        "INSERT OR REPLACE INTO configuracion (clave, valor) VALUES (?, ?)",
        (clave, valor),
    )
    conn.commit()
