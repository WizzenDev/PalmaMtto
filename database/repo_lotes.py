"""
database/repo_lotes.py
----------------------
Repositorio CRUD para la tabla lotes.
"""

from datetime import datetime
from typing import Optional

from database.connection import db


def siguiente_numero_lote() -> int:
    conn = db.get_connection()
    cur = conn.cursor()
    cur.execute("SELECT MAX(numero_lote) FROM lotes")
    row = cur.fetchone()
    return (row[0] or 0) + 1


def insertar_lote(
    numero_lote: int,
    id_primer_mensaje: Optional[int],
    id_ultimo_mensaje: Optional[int],
    cantidad: int,
    proveedor: str,
) -> int:
    conn = db.get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO lotes
            (numero_lote, id_primer_mensaje, id_ultimo_mensaje,
             cantidad_mensajes, estado, proveedor_ia, fecha_proceso)
        VALUES (?, ?, ?, ?, 'pendiente', ?, ?)
        """,
        (
            numero_lote,
            id_primer_mensaje,
            id_ultimo_mensaje,
            cantidad,
            proveedor,
            datetime.now().isoformat(timespec="seconds"),
        ),
    )
    conn.commit()
    return cur.lastrowid  # type: ignore[return-value]


def actualizar_procesado(id_lote: int, tokens_usados: Optional[int]) -> None:
    conn = db.get_connection()
    conn.execute(
        """
        UPDATE lotes
        SET estado = 'procesado', tokens_usados = ?, fecha_proceso = ?
        WHERE id = ?
        """,
        (tokens_usados, datetime.now().isoformat(timespec="seconds"), id_lote),
    )
    conn.commit()


def actualizar_error(id_lote: int, detalle: str) -> None:
    conn = db.get_connection()
    conn.execute(
        """
        UPDATE lotes
        SET estado = 'error', error_detalle = ?, fecha_proceso = ?
        WHERE id = ?
        """,
        (detalle, datetime.now().isoformat(timespec="seconds"), id_lote),
    )
    conn.commit()


def get_all() -> list[dict]:
    conn = db.get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM lotes ORDER BY id DESC")
    return [dict(row) for row in cur.fetchall()]
