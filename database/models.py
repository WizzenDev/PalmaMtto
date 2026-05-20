"""
database/models.py
------------------
Dataclasses que representan las entidades de la base de datos de PalmaMtto.

Cada dataclass mapea directamente a una tabla SQLite. Los métodos de
serialización/deserialización JSON para campos compuestos (adjuntos) viven
aquí, cerca de la definición de la entidad.

Decisión de diseño: se usan dataclasses estándar (no Pydantic ni attrs) para
mantener dependencias mínimas. La validación de valores de dominio (tipos de
mensaje, estados) se deja al repositorio y a la UI, no al modelo, para evitar
acoplamientos.
"""

import json
from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Mensaje
# ---------------------------------------------------------------------------

@dataclass
class Mensaje:
    """
    Representa un mensaje de WhatsApp parseado y almacenado.

    Atributos con valores predeterminados no se incluyen en el constructor
    posicional; siempre usar kwargs para ellos.
    """

    # Campos obligatorios (sin valor predeterminado)
    fecha: str          # Formato ISO 8601: YYYY-MM-DD
    hora: str           # Formato 24h: HH:MM
    remitente: str      # Nombre o número del remitente
    texto: str          # Contenido textual del mensaje

    # Campos opcionales con valor predeterminado
    adjuntos: list[str] = field(default_factory=list)
    """Lista de nombres de archivos adjuntos (ej: ['IMG-001.jpg'])."""

    media_omitida: bool = False
    """True si el archivo fue exportado como '(media omitted)'."""

    estado_proceso: str = "sin_procesar"
    """Estado del ciclo de vida IA: sin_procesar | procesado | error."""

    id_lote: Optional[int] = None
    """ID del lote con el que fue procesado. NULL si no ha sido procesado."""

    equipo: Optional[str] = None
    """Equipo identificado por la IA o editado manualmente."""

    tipo_mensaje: Optional[str] = None
    """Clasificación: intervencion | informativo | solicitud | relleno | otro."""

    editado_manual: bool = False
    """True si el usuario editó el registro manualmente."""

    fecha_proceso: Optional[str] = None
    """Timestamp ISO del último procesamiento IA."""

    id: Optional[int] = None
    """ID asignado por SQLite. None antes de la inserción."""

    # ------------------------------------------------------------------
    # Serialización para SQLite
    # ------------------------------------------------------------------

    def adjuntos_json(self) -> str:
        """Serializa la lista de adjuntos a JSON para almacenar en SQLite."""
        return json.dumps(self.adjuntos, ensure_ascii=False)

    @staticmethod
    def adjuntos_from_json(json_str: Optional[str]) -> list[str]:
        """
        Deserializa adjuntos desde un string JSON de SQLite.

        Maneja el caso de columna NULL o string inválido retornando lista vacía.
        """
        if not json_str:
            return []
        try:
            resultado = json.loads(json_str)
            return resultado if isinstance(resultado, list) else []
        except json.JSONDecodeError:
            return []

    # ------------------------------------------------------------------
    # Utilidades
    # ------------------------------------------------------------------

    def tiene_adjuntos(self) -> bool:
        """Retorna True si el mensaje tiene al menos un archivo adjunto."""
        return bool(self.adjuntos) or self.media_omitida

    def esta_procesado(self) -> bool:
        """Retorna True si el mensaje ya fue clasificado por la IA."""
        return self.estado_proceso == "procesado"

    def __repr__(self) -> str:
        texto_corto = (self.texto[:40] + "…") if len(self.texto) > 40 else self.texto
        return (
            f"Mensaje(id={self.id}, fecha={self.fecha}, "
            f"remitente='{self.remitente}', texto='{texto_corto}')"
        )


# ---------------------------------------------------------------------------
# Lote
# ---------------------------------------------------------------------------

@dataclass
class Lote:
    """
    Representa un lote de procesamiento IA.

    Un lote agrupa N mensajes consecutivos enviados a un proveedor de IA
    en una sola llamada API.
    """

    numero_lote: int
    """Número secuencial visible para el usuario (1, 2, 3, …)."""

    cantidad_mensajes: int = 0
    id_primer_mensaje: Optional[int] = None
    id_ultimo_mensaje: Optional[int] = None
    estado: str = "pendiente"
    """pendiente | procesado | error | parcial."""

    proveedor_ia: Optional[str] = None
    """Proveedor usado: openai | anthropic | gemini | ollama."""

    tokens_usados: Optional[int] = None
    """Tokens consumidos (solo si el API lo reporta)."""

    fecha_proceso: Optional[str] = None
    """Timestamp ISO del procesamiento."""

    error_detalle: Optional[str] = None
    """Mensaje de error si estado = 'error'."""

    id: Optional[int] = None
    """ID asignado por SQLite."""

    def __repr__(self) -> str:
        return (
            f"Lote(id={self.id}, numero={self.numero_lote}, "
            f"mensajes={self.cantidad_mensajes}, estado={self.estado})"
        )


# ---------------------------------------------------------------------------
# Equipo
# ---------------------------------------------------------------------------

@dataclass
class Equipo:
    """
    Representa un equipo de la planta extractora.

    Los equipos activos se incluyen en el prompt de la IA para que pueda
    identificarlos por nombre exacto.
    """

    nombre: str
    """Nombre del equipo, ej: 'Prensa #7', 'Digestor #1'. Debe ser único."""

    descripcion: Optional[str] = None
    """Descripción opcional del equipo."""

    activo: bool = True
    """False si el equipo está desactivado y no debe incluirse en el prompt IA."""

    origen: str = "manual"
    """manual | ia_sugerido (equipos detectados automáticamente por la IA)."""

    fecha_creacion: Optional[str] = None
    """Timestamp ISO de creación (lo asigna SQLite por defecto)."""

    id: Optional[int] = None
    """ID asignado por SQLite."""

    def __repr__(self) -> str:
        estado = "activo" if self.activo else "inactivo"
        return f"Equipo(id={self.id}, nombre='{self.nombre}', {estado})"


# ---------------------------------------------------------------------------
# Configuracion
# ---------------------------------------------------------------------------

@dataclass
class Configuracion:
    """
    Representa un par clave-valor de la tabla configuracion.

    El valor siempre se almacena como texto y se castea en el código
    cuando se necesita un tipo específico.
    """

    clave: str
    """Nombre de la configuración (clave primaria)."""

    valor: str
    """Valor almacenado como texto."""

    # ------------------------------------------------------------------
    # Helpers de conversión de tipo
    # ------------------------------------------------------------------

    def como_int(self, default: int = 0) -> int:
        """Convierte el valor a entero."""
        try:
            return int(self.valor)
        except (ValueError, TypeError):
            return default

    def como_bool(self, default: bool = False) -> bool:
        """Convierte el valor a booleano (1/0 o 'true'/'false')."""
        if self.valor in ("1", "true", "True", "yes"):
            return True
        if self.valor in ("0", "false", "False", "no"):
            return False
        return default

    def como_float(self, default: float = 0.0) -> float:
        """Convierte el valor a flotante."""
        try:
            return float(self.valor)
        except (ValueError, TypeError):
            return default

    def __repr__(self) -> str:
        return f"Configuracion(clave='{self.clave}', valor='{self.valor}')"


# ---------------------------------------------------------------------------
# Siguiente archivo a construir: database/repo_mensajes.py
# ---------------------------------------------------------------------------
