from .connection import get_connection
from .models import Mensaje
from typing import List, Optional
import json

def insert_mensaje(mensaje: Mensaje) -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO mensajes (
            fecha, hora, remitente, texto, adjuntos, media_omitida, estado_proceso, id_lote, equipo, tipo_mensaje, editado_manual, fecha_proceso
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        mensaje.fecha,
        mensaje.hora,
        mensaje.remitente,
        mensaje.texto,
        mensaje.adjuntos,
        mensaje.media_omitida,
        mensaje.estado_proceso,
        mensaje.id_lote,
        mensaje.equipo,
        mensaje.tipo_mensaje,
        mensaje.editado_manual,
        mensaje.fecha_proceso
    ))
    conn.commit()
    return cur.lastrowid

def get_all_mensajes() -> List[Mensaje]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM mensajes')
    rows = cur.fetchall()
    return [Mensaje(**dict(row)) for row in rows]

def get_mensaje_by_id(id: int) -> Optional[Mensaje]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM mensajes WHERE id = ?', (id,))
    row = cur.fetchone()
    return Mensaje(**dict(row)) if row else None

def update_mensaje(mensaje: Mensaje):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('''
        UPDATE mensajes SET
          fecha=?, hora=?, remitente=?, texto=?, adjuntos=?, media_omitida=?, estado_proceso=?, id_lote=?, equipo=?, tipo_mensaje=?, editado_manual=?, fecha_proceso=?
        WHERE id=?
    ''', (
        mensaje.fecha,
        mensaje.hora,
        mensaje.remitente,
        mensaje.texto,
        mensaje.adjuntos,
        mensaje.media_omitida,
        mensaje.estado_proceso,
        mensaje.id_lote,
        mensaje.equipo,
        mensaje.tipo_mensaje,
        mensaje.editado_manual,
        mensaje.fecha_proceso,
        mensaje.id
    ))
    conn.commit()

def delete_mensaje(id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('DELETE FROM mensajes WHERE id = ?', (id,))
    conn.commit()
