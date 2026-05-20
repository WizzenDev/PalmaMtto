"""
config.py
---------
Constantes globales, rutas y valores predeterminados de PalmaMtto Desktop.

Decisión de diseño: config.py vive en la raíz del paquete (junto a main.py)
para que todos los módulos puedan importarlo con un import simple sin
preocuparse por rutas relativas. Las rutas se resuelven con pathlib para
garantizar compatibilidad Windows/Linux/Mac.
"""

from pathlib import Path

# ---------------------------------------------------------------------------
# Rutas base
# ---------------------------------------------------------------------------

# Directorio raíz del proyecto (donde vive este archivo)
BASE_DIR: Path = Path(__file__).parent.resolve()

# Directorio de datos del usuario.
# En producción (PyInstaller) se coloca junto al ejecutable.
# En desarrollo se crea dentro del proyecto.
DATA_DIR: Path = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# Ruta de la base de datos SQLite
DB_PATH: Path = DATA_DIR / "palma_mtto.db"

# ---------------------------------------------------------------------------
# Información de la aplicación
# ---------------------------------------------------------------------------

APP_NAME: str = "PalmaMtto Desktop"
APP_VERSION: str = "1.0.0"

# ---------------------------------------------------------------------------
# Valores de dominio (listas cerradas)
# ---------------------------------------------------------------------------

# Tipos de mensaje posibles para la clasificación IA
TIPOS_MENSAJE: list[str] = [
    "intervencion",  # Trabajo realizado sobre un equipo
    "informativo",   # Reporte de estado, novedad o contexto
    "solicitud",     # Requerimiento de repuesto, recurso o acción
    "relleno",       # Mensaje sin información técnica útil
    "otro",          # No clasifica en ninguna categoría anterior
]

# Estados del proceso IA para cada mensaje
ESTADOS_PROCESO: list[str] = [
    "sin_procesar",
    "procesado",
    "error",
]

# Estados posibles de un lote
ESTADOS_LOTE: list[str] = [
    "pendiente",
    "procesado",
    "error",
    "parcial",
]

# Orígenes posibles de un equipo
ORIGENES_EQUIPO: list[str] = [
    "manual",
    "ia_sugerido",
]

# ---------------------------------------------------------------------------
# Multimedia
# ---------------------------------------------------------------------------

# Extensiones de archivo reconocidas por el detector de adjuntos
EXTENSIONES_IMAGEN: set[str] = {".jpg", ".jpeg", ".png"}
EXTENSIONES_VIDEO: set[str] = {".mp4"}
EXTENSIONES_DOC: set[str] = {".pdf", ".doc", ".docx", ".xlsx"}

# Todas las extensiones de adjuntos soportadas (para el regex del parser)
EXTENSIONES_ADJUNTOS: set[str] = (
    EXTENSIONES_IMAGEN | EXTENSIONES_VIDEO | EXTENSIONES_DOC
)

# ---------------------------------------------------------------------------
# Procesamiento IA
# ---------------------------------------------------------------------------

# Tamaño de lote predeterminado (mensajes por envío)
TAMANO_LOTE_DEFAULT: int = 50

# Pausa predeterminada entre lotes (segundos)
PAUSA_LOTES_DEFAULT: int = 1

# Reintento máximo cuando el JSON de respuesta es inválido
MAX_REINTENTOS_IA: int = 1

# ---------------------------------------------------------------------------
# Claves de configuración en la tabla `configuracion`
# ---------------------------------------------------------------------------

CONFIG_PROVEEDOR_IA: str = "proveedor_ia"
CONFIG_KEY_OPENAI: str = "api_key_openai"
CONFIG_KEY_ANTHROPIC: str = "api_key_anthropic"
CONFIG_KEY_GEMINI: str = "api_key_gemini"
CONFIG_DIR_MULTIMEDIA: str = "directorio_multimedia"
CONFIG_TAMANO_LOTE: str = "tamano_lote"
CONFIG_PAUSA_LOTES: str = "pausa_entre_lotes"
CONFIG_AGREGAR_EQUIPOS_AUTO: str = "agregar_equipos_automatico"
CONFIG_CONFIRMAR_TODOS: str = "confirmar_procesar_todos"
CONFIG_TEMA: str = "tema"
CONFIG_TAMANO_FUENTE: str = "tamano_fuente_tabla"
CONFIG_PROMPT_BASE: str = "prompt_base"

# ---------------------------------------------------------------------------
# Siguiente archivo a construir: database/connection.py
# ---------------------------------------------------------------------------
