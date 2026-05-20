"""
ui/widgets/message_table.py
---------------------------
Tabla principal de mensajes basada en QAbstractTableModel + QTableView.

Decisión de diseño: se usa QAbstractTableModel (modelo personalizado) en lugar
de QTableWidget para tener control total sobre los datos y soportar paginación
futura. El modelo guarda la lista de Mensaje en memoria; recargas completas
son rápidas para las magnitudes esperadas (< 50 000 mensajes).

La columna "Adjuntos" muestra un texto "📎 N" cuando hay archivos; la tabla
delegará la apertura del visor de multimedia al tab_viewer.py mediante señales.

El modelo expone señales para notificar cambios de datos sin acoplar la tabla
a la BD directamente.
"""

from typing import Any, Optional

from PyQt6.QtCore import (
    QAbstractTableModel,
    QModelIndex,
    QSortFilterProxyModel,
    Qt,
    pyqtSignal,
)
from PyQt6.QtGui import QBrush, QColor, QFont
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QHeaderView,
    QMenu,
    QTableView,
    QWidget,
)

from database.models import Mensaje
from ui.styles import (
    COLOR_ACENTO,
    COLOR_BG_HOVER,
    COLOR_TEXTO_SECUNDARIO,
    color_estado_proceso,
)

# ---------------------------------------------------------------------------
# Definición de columnas visibles
# ---------------------------------------------------------------------------

# Cada entrada: (clave_interna, encabezado_visible, ancho_px, ancho_fijo)
COLUMNAS: list[tuple[str, str, int, bool]] = [
    ("fecha",         "Fecha",     90,  True),
    ("hora",          "Hora",      65,  True),
    ("remitente",     "Remitente", 180, True),
    ("texto",         "Texto",     0,   False),   # 0 = expandible
    ("equipo",        "Equipo",    160, True),
    ("tipo_mensaje",  "Tipo",      120, True),
    ("adjuntos",      "Adj.",      55,  True),
    ("estado_proceso","Estado",    100, True),
]

COL_FECHA         = 0
COL_HORA          = 1
COL_REMITENTE     = 2
COL_TEXTO         = 3
COL_EQUIPO        = 4
COL_TIPO          = 5
COL_ADJUNTOS      = 6
COL_ESTADO        = 7


# ---------------------------------------------------------------------------
# Modelo de datos
# ---------------------------------------------------------------------------

class MensajeTableModel(QAbstractTableModel):
    """
    Modelo que alimenta el QTableView con instancias de Mensaje.

    Señales:
        solicitar_edicion(Mensaje):    El usuario pidió editar un mensaje.
        solicitar_ver_adjuntos(Mensaje): El usuario pidió ver los adjuntos.
    """

    # Señales personalizadas
    solicitar_edicion       = pyqtSignal(object)   # object = Mensaje
    solicitar_ver_adjuntos  = pyqtSignal(object)   # object = Mensaje

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._mensajes: list[Mensaje] = []

    # ------------------------------------------------------------------
    # Métodos obligatorios de QAbstractTableModel
    # ------------------------------------------------------------------

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Número de filas (mensajes)."""
        return len(self._mensajes)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Número de columnas definidas."""
        return len(COLUMNAS)

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        """Encabezados de columnas."""
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return COLUMNAS[section][1]   # Encabezado visible
            else:
                return str(section + 1)       # Número de fila
        return None

    def data(
        self,
        index: QModelIndex,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        """Datos de cada celda para distintos roles de Qt."""
        if not index.isValid():
            return None

        msg = self._mensajes[index.row()]
        col = index.column()

        # ------------------------------------------------------------------
        # Rol: Texto visible
        # ------------------------------------------------------------------
        if role == Qt.ItemDataRole.DisplayRole:
            return self._texto_celda(msg, col)

        # ------------------------------------------------------------------
        # Rol: Alineación
        # ------------------------------------------------------------------
        if role == Qt.ItemDataRole.TextAlignmentRole:
            if col in (COL_FECHA, COL_HORA, COL_ADJUNTOS):
                return Qt.AlignmentFlag.AlignCenter
            return Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter

        # ------------------------------------------------------------------
        # Rol: Color de fondo (estado y alternado de fila)
        # ------------------------------------------------------------------
        if role == Qt.ItemDataRole.BackgroundRole:
            if col == COL_ESTADO:
                fondo, _ = color_estado_proceso(msg.estado_proceso)
                return QBrush(QColor(fondo))
            return None

        # ------------------------------------------------------------------
        # Rol: Color de texto
        # ------------------------------------------------------------------
        if role == Qt.ItemDataRole.ForegroundRole:
            if col == COL_ESTADO:
                _, texto = color_estado_proceso(msg.estado_proceso)
                return QBrush(QColor(texto))
            if col == COL_ADJUNTOS and (msg.adjuntos or msg.media_omitida):
                return QBrush(QColor(COLOR_ACENTO))
            if col in (COL_EQUIPO, COL_TIPO) and not self._texto_celda(msg, col):
                return QBrush(QColor(COLOR_TEXTO_SECUNDARIO))
            return None

        # ------------------------------------------------------------------
        # Rol: Fuente
        # ------------------------------------------------------------------
        if role == Qt.ItemDataRole.FontRole:
            if col == COL_ESTADO:
                f = QFont()
                f.setPointSize(10)
                f.setBold(True)
                return f
            return None

        # ------------------------------------------------------------------
        # Rol: Datos crudos (para acceso programático)
        # ------------------------------------------------------------------
        if role == Qt.ItemDataRole.UserRole:
            return msg

        # ------------------------------------------------------------------
        # Rol: Tooltip
        # ------------------------------------------------------------------
        if role == Qt.ItemDataRole.ToolTipRole:
            if col == COL_TEXTO and len(msg.texto) > 80:
                return msg.texto
            if col == COL_ADJUNTOS and msg.adjuntos:
                return "\n".join(msg.adjuntos)
            if col == COL_ESTADO and msg.estado_proceso == "error":
                return "Error en el procesamiento IA"
            return None

        return None

    # ------------------------------------------------------------------
    # Texto de cada celda según columna
    # ------------------------------------------------------------------

    def _texto_celda(self, msg: Mensaje, col: int) -> str:
        """Formatea el valor de una celda para DisplayRole."""
        if col == COL_FECHA:
            # Convertir de YYYY-MM-DD a DD/MM/YYYY para legibilidad
            try:
                partes = msg.fecha.split("-")
                return f"{partes[2]}/{partes[1]}/{partes[0]}"
            except (IndexError, AttributeError):
                return msg.fecha or ""

        elif col == COL_HORA:
            return msg.hora or ""

        elif col == COL_REMITENTE:
            return msg.remitente or ""

        elif col == COL_TEXTO:
            # Mostrar solo la primera línea para no romper el layout
            primera_linea = (msg.texto or "").split("\n")[0]
            return primera_linea

        elif col == COL_EQUIPO:
            return msg.equipo or ""

        elif col == COL_TIPO:
            return (msg.tipo_mensaje or "").replace("_", " ")

        elif col == COL_ADJUNTOS:
            n = len(msg.adjuntos) if msg.adjuntos else 0
            if msg.media_omitida:
                return "📷 ?"
            if n > 0:
                return f"📎 {n}"
            return ""

        elif col == COL_ESTADO:
            etiquetas = {
                "sin_procesar": "SIN PROC.",
                "procesado":    "OK",
                "error":        "ERROR",
            }
            return etiquetas.get(msg.estado_proceso, msg.estado_proceso)

        return ""

    # ------------------------------------------------------------------
    # Carga y actualización de datos
    # ------------------------------------------------------------------

    def cargar_mensajes(self, mensajes: list[Mensaje]) -> None:
        """
        Reemplaza todos los mensajes del modelo y notifica a la vista.

        Args:
            mensajes: Lista completa de instancias Mensaje a mostrar.
        """
        self.beginResetModel()
        self._mensajes = mensajes
        self.endResetModel()

    def actualizar_mensaje(self, mensaje: Mensaje) -> None:
        """
        Actualiza un solo mensaje en la lista (tras edición manual).

        Busca el mensaje por id y actualiza su fila sin recargar todo.

        Args:
            mensaje: Instancia Mensaje con datos actualizados (debe tener id).
        """
        if mensaje.id is None:
            return
        for i, m in enumerate(self._mensajes):
            if m.id == mensaje.id:
                self._mensajes[i] = mensaje
                # Notificar que toda la fila cambió
                self.dataChanged.emit(
                    self.index(i, 0),
                    self.index(i, len(COLUMNAS) - 1),
                )
                return

    def obtener_mensaje(self, row: int) -> Optional[Mensaje]:
        """
        Retorna el Mensaje en la fila dada (índice del modelo fuente).

        Args:
            row: Índice de fila en el modelo.
        """
        if 0 <= row < len(self._mensajes):
            return self._mensajes[row]
        return None

    def total(self) -> int:
        """Número total de mensajes cargados en el modelo."""
        return len(self._mensajes)

    def mensajes(self) -> list[Mensaje]:
        """Retorna una copia de la lista de mensajes cargados."""
        return list(self._mensajes)


# ---------------------------------------------------------------------------
# Vista: QTableView configurada para PalmaMtto
# ---------------------------------------------------------------------------

class MensajeTableView(QTableView):
    """
    Vista de tabla configurada para mostrar mensajes de PalmaMtto.

    Envuelve QTableView con:
    - QSortFilterProxyModel para ordenamiento por columna.
    - Menú contextual con acciones (editar, ver adjuntos, eliminar).
    - Señales para comunicarse con tab_viewer.py.

    Señales heredadas del modelo:
        modelo.solicitar_edicion(Mensaje)
        modelo.solicitar_ver_adjuntos(Mensaje)
    """

    # Señal emitida al pedir eliminar mensaje(s)
    solicitar_eliminar = pyqtSignal(list)   # list[Mensaje]

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        # Modelo fuente
        self._modelo = MensajeTableModel(self)

        # Proxy para ordenamiento (no filtra — el filtro lo hace repo_mensajes)
        self._proxy = QSortFilterProxyModel(self)
        self._proxy.setSourceModel(self._modelo)
        self._proxy.setSortCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.setModel(self._proxy)

        self._configurar_vista()
        self._configurar_columnas()
        self._conectar_senales()

    # ------------------------------------------------------------------
    # Configuración inicial
    # ------------------------------------------------------------------

    def _configurar_vista(self) -> None:
        """Aplica opciones visuales y de comportamiento a la QTableView."""
        # Selección de filas completas
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)

        # Ordenamiento habilitado (clic en encabezado)
        self.setSortingEnabled(True)
        self.sortByColumn(0, Qt.SortOrder.DescendingOrder)  # Más recientes primero

        # Altura de fila uniforme
        self.verticalHeader().setDefaultSectionSize(28)
        self.verticalHeader().setVisible(False)

        # Sin edición directa en celda (se edita por diálogo)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        # Texto largo se corta con "..." (wrap solo en col Texto con doble clic)
        self.setWordWrap(False)

        # Mostrar filas alternas con color diferente (manejado por QSS)
        self.setAlternatingRowColors(True)

        # Menú contextual personalizado
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._mostrar_menu_contextual)

    def _configurar_columnas(self) -> None:
        """Ajusta anchos de columnas según la definición de COLUMNAS."""
        header = self.horizontalHeader()
        for i, (_, _, ancho, fijo) in enumerate(COLUMNAS):
            if fijo:
                header.setSectionResizeMode(i, QHeaderView.ResizeMode.Fixed)
                self.setColumnWidth(i, ancho)
            else:
                header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)

    def _conectar_senales(self) -> None:
        """Conecta señales internas de la tabla."""
        # Doble clic → solicitar edición
        self.doubleClicked.connect(self._al_doble_clic)

    # ------------------------------------------------------------------
    # Interacciones del usuario
    # ------------------------------------------------------------------

    def _al_doble_clic(self, proxy_index: QModelIndex) -> None:
        """Emite solicitar_edicion con el Mensaje de la fila."""
        msg = self._obtener_mensaje_de_proxy(proxy_index)
        if msg:
            self._modelo.solicitar_edicion.emit(msg)

    def _mostrar_menu_contextual(self, pos) -> None:
        """Construye y muestra el menú contextual al hacer clic derecho."""
        index = self.indexAt(pos)
        if not index.isValid():
            return

        msg = self._obtener_mensaje_de_proxy(index)
        if not msg:
            return

        menu = QMenu(self)

        accion_editar = menu.addAction("Editar...")
        accion_adjuntos = menu.addAction("Ver adjuntos")
        accion_marcar = menu.addAction("Marcar como procesado")
        menu.addSeparator()
        accion_eliminar = menu.addAction("Eliminar")

        # Habilitar o deshabilitar adjuntos si no hay archivos
        accion_adjuntos.setEnabled(bool(msg.adjuntos) or msg.media_omitida)

        # Ejecutar acción seleccionada
        accion = menu.exec(self.viewport().mapToGlobal(pos))
        if accion == accion_editar:
            self._modelo.solicitar_edicion.emit(msg)
        elif accion == accion_adjuntos:
            self._modelo.solicitar_ver_adjuntos.emit(msg)
        elif accion == accion_marcar:
            self._marcar_procesado(msg)
        elif accion == accion_eliminar:
            self._emitir_eliminar_seleccionados()

    # ------------------------------------------------------------------
    # Acciones del menú contextual
    # ------------------------------------------------------------------

    def _emitir_eliminar_seleccionados(self) -> None:
        """Emite la señal con los mensajes seleccionados para eliminación."""
        seleccion = self.selectionModel().selectedRows()
        mensajes = []
        for idx in seleccion:
            msg = self._obtener_mensaje_de_proxy(idx)
            if msg:
                mensajes.append(msg)

        if mensajes:
            self.solicitar_eliminar.emit(mensajes)

    def _marcar_procesado(self, msg: Mensaje) -> None:
        """Marca un mensaje como procesado (solo en memoria por ahora)."""
        msg.estado_proceso = "procesado"
        self._modelo.actualizar_mensaje(msg)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _obtener_mensaje_de_proxy(self, proxy_index: QModelIndex) -> Optional[Mensaje]:
        """Convierte índice del proxy al modelo fuente y retorna el Mensaje."""
        if not proxy_index.isValid():
            return None
        source_index = self._proxy.mapToSource(proxy_index)
        return self._modelo.obtener_mensaje(source_index.row())

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    @property
    def modelo(self) -> MensajeTableModel:
        return self._modelo

    def cargar_mensajes(self, mensajes: list[Mensaje]) -> None:
        """Proxy hacia el modelo para cargar nuevos mensajes."""
        self._modelo.cargar_mensajes(mensajes)

    def actualizar_mensaje(self, mensaje: Mensaje) -> None:
        """Proxy hacia el modelo para actualizar un mensaje."""
        self._modelo.actualizar_mensaje(mensaje)

    def total(self) -> int:
        """Retorna el total de mensajes cargados en el modelo."""
        return self._modelo.total()

    def mensajes(self) -> list[Mensaje]:
        """Retorna la lista de mensajes actualmente visibles."""
        return self._modelo.mensajes()
