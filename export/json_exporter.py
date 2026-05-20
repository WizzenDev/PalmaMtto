"""
export/json_exporter.py
-----------------------
Exporta mensajes a JSON con adjuntos como lista real.
"""

import json
from pathlib import Path
from typing import Iterable, Optional

from database.models import Mensaje

COLUMNAS_DEFAULT = [
    "fecha",
    "hora",
    "remitente",
    "texto",
    "equipo",
    "tipo_mensaje",
    "adjuntos",
    "estado_proceso",
]


def exportar_json(
    mensajes: Iterable[Mensaje],
    ruta: Path,
    columnas: Optional[list[str]] = None,
) -> None:
    """Exporta los mensajes a un archivo JSON."""
    columnas = columnas or COLUMNAS_DEFAULT
    ruta.parent.mkdir(parents=True, exist_ok=True)

    payload = [_mensaje_a_dict(m, columnas) for m in mensajes]
    ruta.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _mensaje_a_dict(m: Mensaje, columnas: list[str]) -> dict:
    """Convierte un Mensaje en dict según columnas definidas."""
    salida: dict = {}
    for col in columnas:
        if col == "adjuntos":
            salida[col] = list(m.adjuntos)
        else:
            salida[col] = getattr(m, col, None)
    return salida
