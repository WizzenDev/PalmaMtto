"""
export/csv_exporter.py
----------------------
Exporta mensajes a CSV (UTF-8 con BOM) para compatibilidad con Excel.
"""

import csv
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


def exportar_csv(
    mensajes: Iterable[Mensaje],
    ruta: Path,
    columnas: Optional[list[str]] = None,
) -> None:
    """Exporta los mensajes a un archivo CSV."""
    columnas = columnas or COLUMNAS_DEFAULT
    ruta.parent.mkdir(parents=True, exist_ok=True)

    with ruta.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(columnas)
        for m in mensajes:
            writer.writerow(_mensaje_a_fila(m, columnas))


def _mensaje_a_fila(m: Mensaje, columnas: list[str]) -> list[str]:
    """Convierte un Mensaje en una fila CSV según las columnas definidas."""
    salida: list[str] = []
    for col in columnas:
        if col == "adjuntos":
            salida.append("|".join(m.adjuntos) if m.adjuntos else "")
        else:
            valor = getattr(m, col, "")
            salida.append("" if valor is None else str(valor))
    return salida
