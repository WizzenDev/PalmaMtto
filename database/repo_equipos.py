"""
database/repo_equipos.py
------------------------
Repositorio CRUD para la tabla `equipos`.

Incluye utilidades para activar/desactivar equipos, renombrar y fusionar,
actualizando los mensajes asociados cuando corresponde.
"""

from typing import Optional

from database.connection import db
from database.models import Equipo


# ---------------------------------------------------------------------------
# Escritura
# ---------------------------------------------------------------------------


def insertar(equipo: Equipo) -> int:
    """Inserta un equipo nuevo y retorna el ID asignado."""
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO equipos (nombre, descripcion, activo, origen)
        VALUES (?, ?, ?, ?)
        """,
        (equipo.nombre, equipo.descripcion, int(equipo.activo), equipo.origen),
    )
    conn.commit()
    return cursor.lastrowid  # type: ignore[return-value]


def actualizar(equipo: Equipo) -> bool:
    """Actualiza un equipo por ID."""
    if equipo.id is None:
        raise ValueError("El equipo no tiene ID asignado; no se puede actualizar.")

    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE equipos
        SET nombre = ?, descripcion = ?, activo = ?, origen = ?
        WHERE id = ?
        """,
        (
            equipo.nombre,
            equipo.descripcion,
            int(equipo.activo),
            equipo.origen,
            equipo.id,
        ),
    )
    conn.commit()
    return cursor.rowcount > 0


def activar(id_equipo: int, activo: bool) -> bool:
    """Activa o desactiva un equipo por ID."""
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE equipos SET activo = ? WHERE id = ?",
        (int(activo), id_equipo),
    )
    conn.commit()
    return cursor.rowcount > 0


def eliminar(id_equipo: int) -> bool:
    """Elimina un equipo por ID (no valida uso)."""
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM equipos WHERE id = ?", (id_equipo,))
    conn.commit()
    return cursor.rowcount > 0


def renombrar(id_equipo: int, nuevo_nombre: str) -> bool:
    """
    Renombra un equipo y actualiza los mensajes que lo referencian.
    """
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT nombre FROM equipos WHERE id = ?", (id_equipo,))
    row = cursor.fetchone()
    if not row:
        return False
    nombre_anterior = row[0]

    cursor.execute(
        "UPDATE equipos SET nombre = ? WHERE id = ?",
        (nuevo_nombre, id_equipo),
    )
    cursor.execute(
        "UPDATE mensajes SET equipo = ? WHERE equipo = ?",
        (nuevo_nombre, nombre_anterior),
    )
    conn.commit()
    return True


def fusionar(nombre_origen: str, nombre_destino: str) -> bool:
    """
    Fusiona dos equipos: reasigna mensajes y elimina el equipo origen.
    """
    if nombre_origen == nombre_destino:
        return False

    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE mensajes SET equipo = ? WHERE equipo = ?",
        (nombre_destino, nombre_origen),
    )
    cursor.execute("DELETE FROM equipos WHERE nombre = ?", (nombre_origen,))
    conn.commit()
    return True


# ---------------------------------------------------------------------------
# Lectura
# ---------------------------------------------------------------------------


def get_by_id(id_equipo: int) -> Optional[Equipo]:
    """Retorna un equipo por ID, o None si no existe."""
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM equipos WHERE id = ?", (id_equipo,))
    row = cursor.fetchone()
    return _row_to_equipo(row) if row else None


def get_by_nombre(nombre: str) -> Optional[Equipo]:
    """Retorna un equipo por nombre exacto."""
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM equipos WHERE nombre = ?", (nombre,))
    row = cursor.fetchone()
    return _row_to_equipo(row) if row else None


def get_all(include_inactivos: bool = True) -> list[Equipo]:
    """Retorna todos los equipos, opcionalmente excluyendo inactivos."""
    conn = db.get_connection()
    cursor = conn.cursor()
    if include_inactivos:
        cursor.execute("SELECT * FROM equipos ORDER BY nombre COLLATE NOCASE")
    else:
        cursor.execute(
            "SELECT * FROM equipos WHERE activo = 1 ORDER BY nombre COLLATE NOCASE"
        )
    return [_row_to_equipo(row) for row in cursor.fetchall()]


def contar_mensajes_por_equipo(nombre: str) -> int:
    """Cuenta cuántos mensajes referencian un equipo por nombre."""
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM mensajes WHERE equipo = ?", (nombre,))
    return cursor.fetchone()[0]


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------


def _row_to_equipo(row) -> Equipo:
    """Convierte una fila de SQLite en dataclass Equipo."""
    return Equipo(
        id=row["id"],
        nombre=row["nombre"],
        descripcion=row["descripcion"],
        activo=bool(row["activo"]),
        origen=row["origen"],
        fecha_creacion=row["fecha_creacion"],
    )
