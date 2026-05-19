from dataclasses import dataclass
from typing import Optional

@dataclass
class Mensaje:
    id: Optional[int]
    fecha: str
    hora: str
    remitente: str
    texto: str
    adjuntos: str
    media_omitida: int
    estado_proceso: str
    id_lote: Optional[int]
    equipo: Optional[str]
    tipo_mensaje: Optional[str]
    editado_manual: int
    fecha_proceso: Optional[str]

@dataclass
class Lote:
    id: Optional[int]
    numero_lote: int
    id_primer_mensaje: int
    id_ultimo_mensaje: int
    cantidad_mensajes: int
    estado: str
    proveedor_ia: Optional[str]
    tokens_usados: Optional[int]
    fecha_proceso: Optional[str]
    error_detalle: Optional[str]

@dataclass
class Equipo:
    id: Optional[int]
    nombre: str
    descripcion: Optional[str]
    activo: int
    origen: str
    fecha_creacion: str

@dataclass
class Configuracion:
    clave: str
    valor: str
