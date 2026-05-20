"""
parser/whatsapp_parser.py
-------------------------
Lógica principal de parseo del archivo .txt exportado de WhatsApp.

Formato de línea válida (exportación de WhatsApp en inglés/español):
    1/16/26, 4:33 PM - Jimmy CeresAgro: Se montan 120GL de Acpm
    16/1/2026, 16:33 - Jimmy CeresAgro: Se montan 120GL de Acpm

Algoritmo:
    1. Leer el archivo completo con UTF-8 (fallback a latin-1).
    2. Iterar línea por línea.
    3. Si la línea coincide con el patrón de fecha → nuevo mensaje.
    4. Si NO coincide → línea de continuación del mensaje actual.
    5. Antes de guardar, pasar por message_cleaner y attachment_detector.
    6. Normalizar fecha a YYYY-MM-DD y hora a HH:MM (24h).
    7. Insertar en BD mediante repo_mensajes (en lote al finalizar).
    8. Retornar un ResumenParseo con las estadísticas.

Decisión de diseño: el parser retorna un ResumenParseo en lugar de lanzar
excepciones por cada línea problemática. Los errores no fatales se acumulan
en la lista `advertencias` para que la UI los muestre al usuario.

La inserción a BD se hace en un único insertar_lote_mensajes() al final
(no por mensaje) para maximizar el rendimiento con archivos grandes.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

from database import repo_mensajes
from database.models import Mensaje
from parser.attachment_detector import detectar_adjuntos
from parser.message_cleaner import es_ruido, limpiar_texto_sistema


# ---------------------------------------------------------------------------
# Patrón de línea principal de WhatsApp
# ---------------------------------------------------------------------------
# Soporta ambos formatos de fecha: M/D/YY, D/M/YYYY, etc.
# Soporta hora en formato 12h (AM/PM) y 24h.
# El nombre del remitente puede contener espacios y guiones.
#
# Grupos capturados:
#   1: fecha   (ej: "1/16/26" o "16/1/2026")
#   2: hora    (ej: "4:33 PM" o "16:33")
#   3: remitente
#   4: texto del mensaje

_PATRON_LINEA: re.Pattern = re.compile(
    r"^(\d{1,2}/\d{1,2}/\d{2,4}),\s"          # fecha
    r"(\d{1,2}:\d{2}(?:\s?[AP]M)?)\s"          # hora (12h o 24h)
    r"-\s"                                       # separador
    r"(.+?)"                                     # remitente (no greedy)
    r":\s"                                       # dos puntos + espacio
    r"(.*)",                                     # texto (puede ser vacío)
    re.IGNORECASE,
)

# Patrón auxiliar para detectar el separador "- " entre fecha/hora y remitente
# en líneas de sistema que no tienen el formato completo
_PATRON_SISTEMA: re.Pattern = re.compile(
    r"^\d{1,2}/\d{1,2}/\d{2,4},\s\d{1,2}:\d{2}",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Resumen de parseo
# ---------------------------------------------------------------------------

@dataclass
class ResumenParseo:
    """Estadísticas del proceso de parseo para mostrar al usuario."""
    total_lineas: int = 0
    mensajes_cargados: int = 0
    mensajes_descartados: int = 0
    mensajes_con_adjuntos: int = 0
    mensajes_con_media_omitida: int = 0
    advertencias: list[str] = field(default_factory=list)
    archivo: str = ""

    def __str__(self) -> str:
        return (
            f"Archivo: {self.archivo}\n"
            f"  Líneas procesadas:       {self.total_lineas}\n"
            f"  Mensajes cargados:       {self.mensajes_cargados}\n"
            f"  Mensajes descartados:    {self.mensajes_descartados}\n"
            f"  Con adjuntos:            {self.mensajes_con_adjuntos}\n"
            f"  Con media omitida:       {self.mensajes_con_media_omitida}\n"
            f"  Advertencias:            {len(self.advertencias)}"
        )


# ---------------------------------------------------------------------------
# Funciones de normalización de fecha y hora
# ---------------------------------------------------------------------------

def _normalizar_fecha(fecha_raw: str) -> str:
    """
    Convierte la fecha del formato de WhatsApp a ISO 8601 (YYYY-MM-DD).

    WhatsApp puede exportar: M/D/YY, D/M/YYYY, M/D/YYYY.
    Se asume el formato M/D/YY o M/D/YYYY (formato EE.UU. común en Colombia
    con WhatsApp en inglés). Si el año tiene 2 dígitos, se interpreta como
    20XX (válido para exportaciones de los años 2000-2099).

    Args:
        fecha_raw: Fecha en formato de exportación (ej: "1/16/26", "16/1/2026").

    Returns:
        Fecha en formato ISO (ej: "2026-01-16").

    Raises:
        ValueError: Si el formato no es reconocible.
    """
    partes = fecha_raw.strip().split("/")
    if len(partes) != 3:
        raise ValueError(f"Formato de fecha no reconocido: '{fecha_raw}'")

    parte_a, parte_b, parte_c = partes

    # Expandir año de 2 dígitos
    anno = int(parte_c)
    if anno < 100:
        anno += 2000

    # Detectar si el formato es M/D o D/M
    # Heurística: si parte_a > 12, es el día (formato D/M/YYYY)
    dia_a = int(parte_a)
    dia_b = int(parte_b)

    if dia_a > 12:
        # Es día/mes/año
        dia, mes = dia_a, dia_b
    elif dia_b > 12:
        # Es mes/día/año (formato EE.UU.)
        mes, dia = dia_a, dia_b
    else:
        # Ambiguo; asumir mes/día/año (formato más común en exportaciones
        # de WhatsApp con idioma inglés en Colombia)
        mes, dia = dia_a, dia_b

    return f"{anno:04d}-{mes:02d}-{dia:02d}"


def _normalizar_hora(hora_raw: str) -> str:
    """
    Convierte la hora del formato de WhatsApp a formato 24h (HH:MM).

    Soporta:
        - "4:33 PM"  → "16:33"
        - "4:33 AM"  → "04:33"
        - "16:33"    → "16:33" (ya está en 24h)
        - "4:33PM"   → "16:33" (sin espacio)

    Args:
        hora_raw: Hora en formato de exportación.

    Returns:
        Hora en formato 24h HH:MM.
    """
    hora_limpia = hora_raw.strip().upper()

    if "AM" in hora_limpia or "PM" in hora_limpia:
        # Formato 12h
        es_pm = "PM" in hora_limpia
        hora_solo = hora_limpia.replace("PM", "").replace("AM", "").strip()
        partes = hora_solo.split(":")
        horas = int(partes[0])
        minutos = int(partes[1]) if len(partes) > 1 else 0

        if es_pm and horas != 12:
            horas += 12
        elif not es_pm and horas == 12:
            horas = 0

        return f"{horas:02d}:{minutos:02d}"
    else:
        # Ya es formato 24h; solo normalizar el padding
        partes = hora_limpia.split(":")
        horas = int(partes[0])
        minutos = int(partes[1]) if len(partes) > 1 else 0
        return f"{horas:02d}:{minutos:02d}"


# ---------------------------------------------------------------------------
# Función principal de parseo
# ---------------------------------------------------------------------------

def parsear_archivo(
    ruta_archivo: Path,
    reemplazar: bool = False,
    callback_progreso: Optional[Callable[[int, int], None]] = None,
) -> ResumenParseo:
    """
    Parsea un archivo .txt exportado de WhatsApp y lo carga en la base de datos.

    Args:
        ruta_archivo:       Ruta al archivo .txt a parsear.
        reemplazar:         Si True, elimina todos los mensajes existentes antes
                            de insertar. Si False, agrega los mensajes nuevos.
        callback_progreso:  Función opcional llamada con (lineas_procesadas, total_lineas)
                            para actualizar una barra de progreso en la UI.

    Returns:
        ResumenParseo con las estadísticas del proceso.

    Raises:
        FileNotFoundError:  Si el archivo no existe.
        UnicodeDecodeError: Si el archivo no puede leerse (error no recuperable).
    """
    resumen = ResumenParseo(archivo=ruta_archivo.name)

    # ------------------------------------------------------------------
    # 1. Leer el archivo
    # ------------------------------------------------------------------
    lineas = _leer_archivo(ruta_archivo)
    resumen.total_lineas = len(lineas)

    # ------------------------------------------------------------------
    # 2. Opcionalmente limpiar mensajes existentes
    # ------------------------------------------------------------------
    if reemplazar:
        repo_mensajes.eliminar_todos()

    # ------------------------------------------------------------------
    # 3. Parseo línea por línea
    # ------------------------------------------------------------------
    mensajes_a_insertar: list[Mensaje] = []
    mensaje_actual: Optional[_MensajeEnConstruccion] = None

    for num_linea, linea in enumerate(lineas, start=1):
        # Notificar progreso cada 500 líneas para no saturar la UI
        if callback_progreso and num_linea % 500 == 0:
            callback_progreso(num_linea, resumen.total_lineas)

        linea = linea.rstrip("\n\r")

        match = _PATRON_LINEA.match(linea)

        if match:
            # --- Nueva línea de mensaje ---
            # Guardar el mensaje anterior si existe
            if mensaje_actual is not None:
                resultado = _finalizar_mensaje(mensaje_actual, resumen)
                if resultado is not None:
                    mensajes_a_insertar.append(resultado)

            # Iniciar el nuevo mensaje
            fecha_raw, hora_raw, remitente, texto = match.groups()

            try:
                fecha = _normalizar_fecha(fecha_raw)
                hora = _normalizar_hora(hora_raw)
            except ValueError as e:
                resumen.advertencias.append(
                    f"Línea {num_linea}: error de fecha/hora — {e}"
                )
                mensaje_actual = None
                continue

            mensaje_actual = _MensajeEnConstruccion(
                fecha=fecha,
                hora=hora,
                remitente=remitente.strip(),
                lineas_texto=[texto],
            )

        elif mensaje_actual is not None:
            # --- Línea de continuación ---
            linea_limpia = limpiar_texto_sistema(linea)
            if linea_limpia:
                mensaje_actual.lineas_texto.append(linea_limpia)

        else:
            # Línea antes del primer mensaje (encabezado del archivo, etc.)
            # Se ignora silenciosamente.
            pass

    # Guardar el último mensaje pendiente
    if mensaje_actual is not None:
        resultado = _finalizar_mensaje(mensaje_actual, resumen)
        if resultado is not None:
            mensajes_a_insertar.append(resultado)

    # ------------------------------------------------------------------
    # 4. Notificar progreso final
    # ------------------------------------------------------------------
    if callback_progreso:
        callback_progreso(resumen.total_lineas, resumen.total_lineas)

    # ------------------------------------------------------------------
    # 5. Insertar en base de datos (una sola transacción)
    # ------------------------------------------------------------------
    if mensajes_a_insertar:
        repo_mensajes.insertar_lote_mensajes(mensajes_a_insertar)

    resumen.mensajes_cargados = len(mensajes_a_insertar)
    return resumen


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------

@dataclass
class _MensajeEnConstruccion:
    """Estado temporal de un mensaje mientras se acumulan sus líneas."""
    fecha: str
    hora: str
    remitente: str
    lineas_texto: list[str]


def _finalizar_mensaje(
    mc: _MensajeEnConstruccion,
    resumen: ResumenParseo,
) -> Optional[Mensaje]:
    """
    Procesa un _MensajeEnConstruccion completo y retorna un Mensaje listo
    para insertar, o None si el mensaje debe descartarse como ruido.

    Pasos:
        1. Unir las líneas de texto.
        2. Detectar y extraer adjuntos.
        3. Verificar si es ruido.
        4. Construir el Mensaje final.
    """
    # 1. Unir líneas de continuación con salto de línea
    texto_crudo = "\n".join(mc.lineas_texto).strip()

    # 2. Detectar adjuntos y limpiar el texto
    resultado_adj = detectar_adjuntos(texto_crudo)
    texto_limpio = resultado_adj.texto_limpio

    # 3. Filtrar ruido
    if es_ruido(mc.remitente, texto_limpio):
        resumen.mensajes_descartados += 1
        return None

    # 4. Construir Mensaje
    mensaje = Mensaje(
        fecha=mc.fecha,
        hora=mc.hora,
        remitente=mc.remitente,
        texto=texto_limpio,
        adjuntos=resultado_adj.adjuntos,
        media_omitida=resultado_adj.media_omitida,
    )

    # Actualizar estadísticas
    if resultado_adj.adjuntos:
        resumen.mensajes_con_adjuntos += 1
    if resultado_adj.media_omitida:
        resumen.mensajes_con_media_omitida += 1

    return mensaje


def _leer_archivo(ruta: Path) -> list[str]:
    """
    Lee el archivo .txt con UTF-8 y cae a latin-1 si falla.

    WhatsApp puede exportar en UTF-8 o en latin-1 dependiendo del sistema
    operativo y la versión. Este fallback cubre la mayoría de los casos.

    Args:
        ruta: Ruta al archivo.

    Returns:
        Lista de líneas del archivo (incluyendo '\n').

    Raises:
        FileNotFoundError: Si el archivo no existe.
    """
    if not ruta.exists():
        raise FileNotFoundError(f"Archivo no encontrado: {ruta}")

    try:
        return ruta.read_text(encoding="utf-8").splitlines(keepends=True)
    except UnicodeDecodeError:
        # Fallback a latin-1 (encoding antiguo, común en exportaciones de Android)
        return ruta.read_text(encoding="latin-1").splitlines(keepends=True)


# ---------------------------------------------------------------------------
# Siguiente archivo a construir: main.py (punto de entrada de la app)
# ---------------------------------------------------------------------------
