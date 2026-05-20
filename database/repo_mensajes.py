"""
database/repo_mensajes.py
-------------------------
Repositorio CRUD para la tabla `mensajes`.

Todas las funciones son síncronas y operan sobre la conexión singleton.
Los QThread del parser y de la IA llaman estas funciones directamente;
SQLite maneja la concurrencia en modo WAL sin bloqueos visibles al usuario.

Decisión de diseño: se prefieren funciones sueltas (no una clase Repository)
para mantener la API simple y evitar boilerplate innecesario. Si el proyecto
crece, es fácil moverlas a una clase.
"""

import sqlite3
from typing import Optional

from database.connection import db
from database.models import Mensaje


# ---------------------------------------------------------------------------
# Escritura
# ---------------------------------------------------------------------------

def insertar(mensaje: Mensaje) -> int:
    """
    Inserta un nuevo mensaje en la base de datos.

    Args:
        mensaje: Instancia de Mensaje (id debe ser None).

    Returns:
        El ID entero asignado por SQLite (AUTOINCREMENT).
    """
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO mensajes
            (fecha, hora, remitente, texto, adjuntos, media_omitida,
             estado_proceso, id_lote, equipo, tipo_mensaje,
             editado_manual, fecha_proceso)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        _mensaje_to_tuple(mensaje),
    )
    conn.commit()
    return cursor.lastrowid  # type: ignore[return-value]


def insertar_lote_mensajes(mensajes: list[Mensaje]) -> int:
    """
    Inserta múltiples mensajes en una sola transacción.

    Mucho más eficiente que llamar insertar() en un bucle cuando se parsea
    un archivo completo (potencialmente miles de mensajes).

    Args:
        mensajes: Lista de instancias Mensaje.

    Returns:
        Número de filas insertadas.
    """
    if not mensajes:
        return 0

    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.executemany(
        """
        INSERT INTO mensajes
            (fecha, hora, remitente, texto, adjuntos, media_omitida,
             estado_proceso, id_lote, equipo, tipo_mensaje,
             editado_manual, fecha_proceso)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [_mensaje_to_tuple(m) for m in mensajes],
    )
    conn.commit()
    return len(mensajes)


def actualizar(mensaje: Mensaje) -> bool:
    """
    Actualiza un mensaje existente por su ID.

    Args:
        mensaje: Instancia de Mensaje con id != None.

    Returns:
        True si se actualizó exactamente una fila, False si no se encontró el ID.

    Raises:
        ValueError: Si mensaje.id es None.
    """
    if mensaje.id is None:
        raise ValueError("El mensaje no tiene ID asignado; no se puede actualizar.")

    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE mensajes SET
            fecha           = ?,
            hora            = ?,
            remitente       = ?,
            texto           = ?,
            adjuntos        = ?,
            media_omitida   = ?,
            estado_proceso  = ?,
            id_lote         = ?,
            equipo          = ?,
            tipo_mensaje    = ?,
            editado_manual  = ?,
            fecha_proceso   = ?
        WHERE id = ?
        """,
        _mensaje_to_tuple(mensaje) + (mensaje.id,),
    )
    conn.commit()
    return cursor.rowcount > 0


def actualizar_clasificacion_ia(
    id_mensaje: int,
    equipo: Optional[str],
    tipo_mensaje: str,
    id_lote: int,
    fecha_proceso: str,
) -> bool:
    """
    Actualiza solo los campos de clasificación IA de un mensaje.

    Más eficiente que actualizar todo el registro cuando la IA
    solo necesita escribir equipo, tipo y estado.

    Args:
        id_mensaje:    ID del mensaje a actualizar.
        equipo:        Nombre del equipo identificado (o None).
        tipo_mensaje:  Tipo asignado por la IA.
        id_lote:       ID del lote que procesó este mensaje.
        fecha_proceso: Timestamp ISO del procesamiento.

    Returns:
        True si se actualizó la fila correctamente.
    """
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE mensajes
        SET equipo         = ?,
            tipo_mensaje   = ?,
            estado_proceso = 'procesado',
            id_lote        = ?,
            fecha_proceso  = ?
        WHERE id = ?
        """,
        (equipo, tipo_mensaje, id_lote, fecha_proceso, id_mensaje),
    )
    conn.commit()
    return cursor.rowcount > 0


def marcar_error_ia(
    id_mensaje: int,
    id_lote: int,
    fecha_proceso: str,
) -> bool:
    """Marca un mensaje como error de procesamiento IA."""
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE mensajes
        SET estado_proceso = 'error',
            id_lote        = ?,
            fecha_proceso  = ?
        WHERE id = ?
        """,
        (id_lote, fecha_proceso, id_mensaje),
    )
    conn.commit()
    return cursor.rowcount > 0


def eliminar(id_mensaje: int) -> bool:
    """
    Elimina un mensaje por su ID.

    Returns:
        True si fue eliminado, False si no existía.
    """
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM mensajes WHERE id = ?", (id_mensaje,))
    conn.commit()
    return cursor.rowcount > 0


def eliminar_todos() -> int:
    """
    Elimina todos los mensajes de la tabla.

    Se llama cuando el usuario decide 'reemplazar' en lugar de 'agregar'
    al cargar un nuevo archivo .txt.

    Returns:
        Número de filas eliminadas.
    """
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM mensajes")
    conn.commit()
    return cursor.rowcount


# ---------------------------------------------------------------------------
# Lectura
# ---------------------------------------------------------------------------

def get_by_id(id_mensaje: int) -> Optional[Mensaje]:
    """Retorna un mensaje por su ID, o None si no existe."""
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM mensajes WHERE id = ?", (id_mensaje,))
    row = cursor.fetchone()
    return _row_to_mensaje(row) if row else None


def get_all(
    limite: Optional[int] = None,
    offset: int = 0,
) -> list[Mensaje]:
    """
    Retorna mensajes ordenados cronológicamente.

    Args:
        limite: Máximo de registros. None = todos (sin LIMIT).
        offset: Número de registros a saltar (para paginación).
    """
    conn = db.get_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM mensajes ORDER BY fecha ASC, hora ASC"
    params: list = []
    if limite is not None:
        query += " LIMIT ? OFFSET ?"
        params = [limite, offset]
    cursor.execute(query, params)
    return [_row_to_mensaje(row) for row in cursor.fetchall()]


def get_sin_procesar(limite: Optional[int] = None) -> list[Mensaje]:
    """Retorna mensajes con estado_proceso = 'sin_procesar'."""
    conn = db.get_connection()
    cursor = conn.cursor()
    query = (
        "SELECT * FROM mensajes "
        "WHERE estado_proceso = 'sin_procesar' "
        "ORDER BY fecha ASC, hora ASC"
    )
    params: list = []
    if limite is not None:
        query += " LIMIT ?"
        params = [limite]
    cursor.execute(query, params)
    return [_row_to_mensaje(row) for row in cursor.fetchall()]


def get_por_filtros(
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] = None,
    remitente: Optional[str] = None,
    equipo: Optional[str] = None,
    tipo_mensaje: Optional[object] = None,
    estado_proceso: Optional[object] = None,
    equipo_sin_clasificar: bool = False,
    solo_con_multimedia: bool = False,
    keyword: Optional[str] = None,
) -> list[Mensaje]:
    """
    Retorna mensajes que cumplen todos los filtros especificados.

    Los parámetros en None se omiten del WHERE (no filtran).
    Todos los filtros se combinan con AND.

    Args:
        fecha_desde:        Fecha mínima ISO (YYYY-MM-DD), inclusiva.
        fecha_hasta:        Fecha máxima ISO (YYYY-MM-DD), inclusiva.
        remitente:          Nombre exacto del remitente.
        equipo:             Nombre exacto del equipo.
        tipo_mensaje:       Tipo exacto del mensaje.
        estado_proceso:     Estado exacto.
        solo_con_multimedia: Si True, solo mensajes con adjuntos o media_omitida.
        keyword:            Búsqueda parcial en texto y remitente (LIKE %keyword%).

    Returns:
        Lista de Mensaje ordenados por fecha y hora.
    """
    condiciones: list[str] = []
    params: list = []

    if fecha_desde:
        condiciones.append("fecha >= ?")
        params.append(fecha_desde)
    if fecha_hasta:
        condiciones.append("fecha <= ?")
        params.append(fecha_hasta)
    if remitente:
        condiciones.append("remitente = ?")
        params.append(remitente)
    if equipo:
        condiciones.append("equipo = ?")
        params.append(equipo)
    if equipo_sin_clasificar:
        condiciones.append("(equipo IS NULL OR equipo = '')")
    if tipo_mensaje:
        if isinstance(tipo_mensaje, (list, tuple, set)):
            placeholders = ", ".join(["?"] * len(tipo_mensaje))
            condiciones.append(f"tipo_mensaje IN ({placeholders})")
            params.extend(list(tipo_mensaje))
        else:
            condiciones.append("tipo_mensaje = ?")
            params.append(tipo_mensaje)
    if estado_proceso:
        if isinstance(estado_proceso, (list, tuple, set)):
            placeholders = ", ".join(["?"] * len(estado_proceso))
            condiciones.append(f"estado_proceso IN ({placeholders})")
            params.extend(list(estado_proceso))
        else:
            condiciones.append("estado_proceso = ?")
            params.append(estado_proceso)
    if solo_con_multimedia:
        condiciones.append("(adjuntos != '[]' OR media_omitida = 1)")
    if keyword:
        condiciones.append("(texto LIKE ? OR remitente LIKE ?)")
        params.extend([f"%{keyword}%", f"%{keyword}%"])

    where = f"WHERE {' AND '.join(condiciones)}" if condiciones else ""
    query = f"SELECT * FROM mensajes {where} ORDER BY fecha ASC, hora ASC"

    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    return [_row_to_mensaje(row) for row in cursor.fetchall()]


# ---------------------------------------------------------------------------
# Consultas de estadísticas
# ---------------------------------------------------------------------------

def contar() -> int:
    """Retorna el total de mensajes en la base de datos."""
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM mensajes")
    return cursor.fetchone()[0]


def contar_por_estado() -> dict[str, int]:
    """
    Retorna un diccionario con el conteo de mensajes por estado_proceso.
    Ej: {'sin_procesar': 450, 'procesado': 120, 'error': 3}
    """
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT estado_proceso, COUNT(*) FROM mensajes GROUP BY estado_proceso"
    )
    return {row[0]: row[1] for row in cursor.fetchall()}


def get_remitentes_unicos() -> list[str]:
    """Retorna la lista de remitentes únicos, ordenados alfabéticamente."""
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT DISTINCT remitente FROM mensajes ORDER BY remitente COLLATE NOCASE"
    )
    return [row[0] for row in cursor.fetchall()]


def get_rango_fechas() -> tuple[Optional[str], Optional[str]]:
    """
    Retorna la fecha mínima y máxima de los mensajes almacenados.

    Returns:
        Tupla (fecha_min, fecha_max) en formato ISO, o (None, None) si no hay datos.
    """
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT MIN(fecha), MAX(fecha) FROM mensajes")
    row = cursor.fetchone()
    return (row[0], row[1]) if row else (None, None)


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------

def _mensaje_to_tuple(m: Mensaje) -> tuple:
    """Convierte un Mensaje a la tupla de parámetros para INSERT/UPDATE."""
    return (
        m.fecha,
        m.hora,
        m.remitente,
        m.texto,
        m.adjuntos_json(),
        int(m.media_omitida),
        m.estado_proceso,
        m.id_lote,
        m.equipo,
        m.tipo_mensaje,
        int(m.editado_manual),
        m.fecha_proceso,
    )


def _row_to_mensaje(row: sqlite3.Row) -> Mensaje:
    """Convierte una fila sqlite3.Row al dataclass Mensaje."""
    return Mensaje(
        id=row["id"],
        fecha=row["fecha"],
        hora=row["hora"],
        remitente=row["remitente"],
        texto=row["texto"] or "",
        adjuntos=Mensaje.adjuntos_from_json(row["adjuntos"]),
        media_omitida=bool(row["media_omitida"]),
        estado_proceso=row["estado_proceso"],
        id_lote=row["id_lote"],
        equipo=row["equipo"],
        tipo_mensaje=row["tipo_mensaje"],
        editado_manual=bool(row["editado_manual"]),
        fecha_proceso=row["fecha_proceso"],
    )


# ---------------------------------------------------------------------------
# Siguiente archivo a construir: parser/message_cleaner.py
# ---------------------------------------------------------------------------
