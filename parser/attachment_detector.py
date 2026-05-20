"""
parser/attachment_detector.py
------------------------------
Detección y extracción de archivos adjuntos en mensajes de WhatsApp.

WhatsApp exporta los adjuntos de dos formas:
  1. Archivo incluido:  "IMG-20260116-WA0028.jpg (file attached)"
  2. Archivo omitido:   "(media omitted)"

Este módulo extrae los nombres de archivo del texto del mensaje,
los retorna como lista y devuelve el texto limpio (sin los marcadores).

Decisión de diseño: se soportan extensiones configurables en config.py.
El regex se construye dinámicamente a partir de ese conjunto para evitar
tener las extensiones duplicadas en dos lugares.
"""

import re
from dataclasses import dataclass

from config import EXTENSIONES_ADJUNTOS


# ---------------------------------------------------------------------------
# Construcción dinámica del regex de adjuntos
# ---------------------------------------------------------------------------

def _construir_regex_adjuntos() -> re.Pattern:
    """
    Construye el regex para detectar adjuntos a partir de las extensiones
    definidas en config.EXTENSIONES_ADJUNTOS.

    Patrón resultante (ejemplo):
        ([\\w\\-\\.]+\\.(?:jpg|jpeg|png|mp4|pdf|doc|docx|xlsx))\\s*\\(file attached\\)

    La parte del nombre de archivo acepta:
        - Letras, dígitos, guiones, guiones bajos, puntos
        - Nombres con espacios entre corchetes no son comunes en WhatsApp;
          se asume que los nombres de archivo exportados no contienen espacios.
    """
    # Quitar los puntos de las extensiones para el regex
    exts = "|".join(
        re.escape(ext.lstrip(".")) for ext in sorted(EXTENSIONES_ADJUNTOS)
    )
    patron = (
        r"([\w\-\.]+\."       # Nombre del archivo (sin espacios)
        r"(?:" + exts + r"))" # Extensión soportada
        r"\s*\(file attached\)"
    )
    return re.compile(patron, re.IGNORECASE)


_RE_FILE_ATTACHED: re.Pattern = _construir_regex_adjuntos()

_RE_MEDIA_OMITTED: re.Pattern = re.compile(
    r"\(media omitted\)",
    re.IGNORECASE,
)

# Patrón auxiliar para limpiar espacios múltiples que quedan tras la extracción
_RE_ESPACIOS_MULTIPLES: re.Pattern = re.compile(r"  +")


# ---------------------------------------------------------------------------
# Resultado de la detección
# ---------------------------------------------------------------------------

@dataclass
class ResultadoAdjuntos:
    """
    Resultado del análisis de adjuntos de un mensaje.

    Attributes:
        adjuntos:       Lista de nombres de archivo encontrados.
        media_omitida:  True si el mensaje contiene "(media omitted)".
        texto_limpio:   Texto del mensaje sin los marcadores de adjuntos.
    """
    adjuntos: list[str]
    media_omitida: bool
    texto_limpio: str


# ---------------------------------------------------------------------------
# Función pública
# ---------------------------------------------------------------------------

def detectar_adjuntos(texto: str) -> ResultadoAdjuntos:
    """
    Analiza el texto de un mensaje y extrae la información de adjuntos.

    Proceso:
        1. Busca todas las ocurrencias de "nombre.ext (file attached)".
        2. Detecta si hay "(media omitted)".
        3. Elimina los marcadores del texto para devolver contenido limpio.
        4. Normaliza espacios residuales.

    Args:
        texto: Texto crudo del mensaje tal como viene del parser.

    Returns:
        ResultadoAdjuntos con la lista de adjuntos, flag de media omitida
        y el texto limpiado de marcadores.

    Ejemplo:
        >>> r = detectar_adjuntos(
        ...     "Se adjunta foto IMG-001.jpg (file attached) del equipo fallado"
        ... )
        >>> r.adjuntos
        ['IMG-001.jpg']
        >>> r.media_omitida
        False
        >>> r.texto_limpio
        'Se adjunta foto del equipo fallado'
    """
    # 1. Extraer nombres de archivo adjuntos
    adjuntos: list[str] = _RE_FILE_ATTACHED.findall(texto)

    # 2. Detectar media omitida
    media_omitida: bool = bool(_RE_MEDIA_OMITTED.search(texto))

    # 3. Limpiar el texto removiendo los marcadores
    texto_limpio = _RE_FILE_ATTACHED.sub("", texto)
    texto_limpio = _RE_MEDIA_OMITTED.sub("", texto_limpio)

    # 4. Normalizar espacios (eliminar dobles espacios y espacios al inicio/fin)
    texto_limpio = _RE_ESPACIOS_MULTIPLES.sub(" ", texto_limpio).strip()

    return ResultadoAdjuntos(
        adjuntos=adjuntos,
        media_omitida=media_omitida,
        texto_limpio=texto_limpio,
    )


def tiene_adjuntos(texto: str) -> bool:
    """
    Verificación rápida: retorna True si el texto contiene adjuntos.

    Útil cuando solo se necesita saber si hay adjuntos sin extraerlos.
    """
    return bool(_RE_FILE_ATTACHED.search(texto)) or bool(
        _RE_MEDIA_OMITTED.search(texto)
    )


# ---------------------------------------------------------------------------
# Siguiente archivo a construir: parser/whatsapp_parser.py
# ---------------------------------------------------------------------------
