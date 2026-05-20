"""
parser/message_cleaner.py
-------------------------
Filtros para descartar mensajes de sistema y ruido de WhatsApp.

Un mensaje "de ruido" es cualquier línea que WhatsApp inserta
automáticamente (cifrado, usuarios agregados, etc.) o que no
aporta información de mantenimiento (menciones puras, texto vacío).

Decisión de diseño: se usan dos listas de patrones — una de strings
simples (para mensajes de sistema conocidos, que son más rápidos de
chequear con 'in') y otra de expresiones regulares compiladas (para
patrones variables). La función es_ruido() combina ambas comprobaciones.
"""

import re
from typing import Final

# ---------------------------------------------------------------------------
# Patrones de mensajes de sistema de WhatsApp (substrings literales)
# Se comparan en minúsculas para mayor robustez.
# ---------------------------------------------------------------------------

_SUBSTRINGS_SISTEMA: Final[tuple[str, ...]] = (
    # Mensajes de cifrado
    "messages and calls are end-to-end encrypted",
    "end-to-end encrypted",
    "los mensajes y llamadas están cifrados",
    # Eventos de grupo
    "created group",
    "created this group",
    "changed the group",
    "changed the subject",
    "changed this group",
    "you were added",
    "added you",
    "added +",
    "left",
    "removed you",
    # Mensajes de llamada perdida
    "missed voice call",
    "missed video call",
    "llamada de voz perdida",
    "videollamada perdida",
    # Número de seguridad / código de verificación
    "your security code",
    "security code changed",
    # Mensajes de cambio de número
    "changed their phone number",
    # Mensajes de eliminación
    "this message was deleted",
    "you deleted this message",
    "este mensaje fue eliminado",
)

# ---------------------------------------------------------------------------
# Patrones regex compilados
# ---------------------------------------------------------------------------

# Menciones puras: líneas que solo contienen @nombre(s) y separadores
_RE_SOLO_MENCIONES: re.Pattern = re.compile(
    r"^\s*(@[\w\s\-áéíóúüñÁÉÍÓÚÜÑ]+(,|\s)*)+\s*$",
    re.IGNORECASE | re.UNICODE,
)

# Texto vacío o solo espacios / puntuación trivial
_RE_TEXTO_TRIVIAL: re.Pattern = re.compile(
    r"^\s*[.,;:!?\-_\s]*\s*$",
    re.UNICODE,
)

# Notificaciones de archivos sin contenido textual real
# (el adjunto ya fue extraído por attachment_detector; el texto limpio
# puede quedar vacío o con solo el marcador)
_RE_SOLO_MARCADOR_ADJUNTO: re.Pattern = re.compile(
    r"^\s*\(file attached\)\s*$|^\s*\(media omitted\)\s*$",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Función pública
# ---------------------------------------------------------------------------

def es_ruido(remitente: str, texto: str) -> bool:
    """
    Determina si un mensaje debe descartarse por ser ruido o sistema.

    Se llama DESPUÉS de que attachment_detector haya limpiado el texto
    (removido los marcadores de adjuntos). Así el texto que llega aquí
    es solo el contenido textual puro del mensaje.

    Args:
        remitente: Nombre o número del remitente del mensaje.
        texto:     Texto del mensaje YA limpiado de marcadores de adjuntos.

    Returns:
        True si el mensaje debe descartarse (es ruido).
        False si el mensaje debe conservarse.
    """
    texto_lower = texto.lower().strip()
    remitente_lower = remitente.lower().strip()

    # 1. Texto completamente vacío
    if not texto_lower:
        return True

    # 2. Texto solo con puntuación / espacios (sin contenido real)
    if _RE_TEXTO_TRIVIAL.match(texto_lower):
        return True

    # 3. Texto que solo era un marcador de adjunto (ya extraído)
    if _RE_SOLO_MARCADOR_ADJUNTO.match(texto_lower):
        return True

    # 4. Substrings de mensajes de sistema de WhatsApp
    #    Se busca tanto en texto como en remitente (algunos mensajes de
    #    sistema ponen el contenido en el campo "remitente")
    for substring in _SUBSTRINGS_SISTEMA:
        if substring in texto_lower or substring in remitente_lower:
            return True

    # 5. Líneas de solo menciones sin texto adicional
    if _RE_SOLO_MENCIONES.match(texto):
        return True

    return False


def limpiar_texto_sistema(texto: str) -> str:
    """
    Elimina del texto cualquier fragmento conocido de mensaje de sistema
    que haya quedado incrustado en una línea de continuación.

    Por ejemplo, si una línea de continuación contiene solo espacios
    o la frase de cifrado al final del archivo, se limpia antes de
    concatenarla al mensaje actual.

    Args:
        texto: Fragmento de texto de una línea de continuación.

    Returns:
        Texto limpio, o cadena vacía si todo el contenido era ruido.
    """
    texto_strip = texto.strip()
    texto_lower = texto_strip.lower()

    for substring in _SUBSTRINGS_SISTEMA:
        if substring in texto_lower:
            return ""

    return texto_strip


# ---------------------------------------------------------------------------
# Siguiente archivo a construir: parser/attachment_detector.py
# ---------------------------------------------------------------------------
