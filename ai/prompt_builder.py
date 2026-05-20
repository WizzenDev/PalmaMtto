"""
ai/prompt_builder.py
--------------------
Construccion del prompt para clasificacion IA.
"""

from config import TIPOS_MENSAJE


def construir_prompt(
    prompt_base: str,
    equipos: list[str],
    mensajes: list[dict],
) -> str:
    """Construye el prompt completo para enviar al proveedor IA."""
    lista_equipos = "\n".join(f"- {e}" for e in equipos) if equipos else "- (ninguno)"

    tipos = "\n".join(
        [
            f"- {t}: { _descripcion_tipo(t) }"
            for t in TIPOS_MENSAJE
        ]
    )

    bloque_mensajes = "\n".join(
        [f"{{\"id\": {m['id']}, \"texto\": {m['texto']!r}}}" for m in mensajes]
    )

    return (
        f"{prompt_base}\n\n"
        "Lista de equipos conocidos (usa exactamente estos nombres cuando aplique):\n"
        f"{lista_equipos}\n\n"
        "Tipos de mensaje posibles:\n"
        f"{tipos}\n\n"
        "Responde UNICAMENTE con un array JSON, sin texto adicional:\n"
        "[{\"id\": 123, \"equipo\": \"Prensa #7\", \"tipo_mensaje\": \"intervencion\"}, ...]\n\n"
        "Si el equipo no esta en la lista pero puedes identificarlo, usa el nombre exacto del mensaje.\n"
        "Si no aplica equipo, usa null.\n\n"
        "Mensajes a clasificar:\n"
        f"[{bloque_mensajes}]"
    )


def _descripcion_tipo(tipo: str) -> str:
    """Descripcion corta para cada tipo de mensaje."""
    mapa = {
        "intervencion": "trabajo realizado sobre un equipo",
        "informativo": "reporte de estado, novedad o contexto",
        "solicitud": "requerimiento de repuesto, recurso o accion",
        "relleno": "mensaje sin informacion tecnica util",
        "otro": "no clasifica en ninguna categoria anterior",
    }
    return mapa.get(tipo, "categoria de mensaje")
