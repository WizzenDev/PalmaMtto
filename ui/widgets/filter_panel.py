"""
ui/widgets/filter_panel.py
--------------------------
Panel lateral de filtros para el visor de mensajes.
"""

from typing import Optional

from PyQt6.QtCore import QDate, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from config import ESTADOS_PROCESO, TIPOS_MENSAJE
from ui.styles import COLOR_ACENTO_CLARO, COLOR_TEXTO_SECUNDARIO


class FilterPanel(QWidget):
    """
    Panel de filtros con señales de cambio.

    Señales:
        filtros_cambiados(): cualquier cambio en filtros.
    """

    filtros_cambiados = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        self._timer_busqueda = QTimer(self)
        self._timer_busqueda.setSingleShot(True)
        self._timer_busqueda.timeout.connect(self._emitir_cambio)

        self._construir_ui()
        self._conectar_senales()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _construir_ui(self) -> None:
        self.setMinimumWidth(220)
        self.setMaximumWidth(320)
        self.setStyleSheet(
            "background-color: #252A2D; border-right: 1px solid #3A4040;"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 14, 12, 12)
        layout.setSpacing(14)

        lbl_titulo = QLabel("FILTROS")
        lbl_titulo.setStyleSheet(
            f"color: {COLOR_ACENTO_CLARO}; font-weight: 700; "
            f"font-size: 10px; letter-spacing: 1.5px;"
        )
        layout.addWidget(lbl_titulo)

        # Rango de fechas
        layout.addWidget(self._lbl_seccion("Rango de fechas"))

        lbl_desde = QLabel("Desde:")
        lbl_desde.setStyleSheet(f"color: {COLOR_TEXTO_SECUNDARIO}; font-size: 11px;")
        self._date_desde = QDateEdit()
        self._date_desde.setDisplayFormat("dd/MM/yyyy")
        self._date_desde.setCalendarPopup(True)
        self._date_desde.setDate(QDate(2020, 1, 1))

        lbl_hasta = QLabel("Hasta:")
        lbl_hasta.setStyleSheet(f"color: {COLOR_TEXTO_SECUNDARIO}; font-size: 11px;")
        self._date_hasta = QDateEdit()
        self._date_hasta.setDisplayFormat("dd/MM/yyyy")
        self._date_hasta.setCalendarPopup(True)
        self._date_hasta.setDate(QDate.currentDate())

        layout.addWidget(lbl_desde)
        layout.addWidget(self._date_desde)
        layout.addWidget(lbl_hasta)
        layout.addWidget(self._date_hasta)

        # Remitente
        layout.addWidget(self._lbl_seccion("Remitente"))
        self._combo_remitente = QComboBox()
        self._combo_remitente.addItem("Todos")
        self._combo_remitente.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        layout.addWidget(self._combo_remitente)

        # Equipo
        layout.addWidget(self._lbl_seccion("Equipo"))
        self._combo_equipo = QComboBox()
        self._combo_equipo.addItem("Todos")
        self._combo_equipo.addItem("Sin clasificar")
        self._combo_equipo.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        layout.addWidget(self._combo_equipo)

        # Tipos de mensaje
        layout.addWidget(self._lbl_seccion("Tipo de mensaje"))
        self._checks_tipo: dict[str, QCheckBox] = {}
        for tipo in TIPOS_MENSAJE:
            chk = QCheckBox(tipo)
            chk.setChecked(True)
            self._checks_tipo[tipo] = chk
            layout.addWidget(chk)

        # Estado
        layout.addWidget(self._lbl_seccion("Estado"))
        self._checks_estado: dict[str, QCheckBox] = {}
        for estado in ESTADOS_PROCESO:
            chk = QCheckBox(estado)
            chk.setChecked(True)
            self._checks_estado[estado] = chk
            layout.addWidget(chk)

        # Solo multimedia
        self._check_multimedia = QCheckBox("Solo con multimedia")
        layout.addWidget(self._check_multimedia)

        # Búsqueda
        layout.addWidget(self._lbl_seccion("Búsqueda"))
        self._campo_busqueda = QLineEdit()
        self._campo_busqueda.setPlaceholderText("Buscar en texto del mensaje...")
        self._campo_busqueda.setClearButtonEnabled(True)
        layout.addWidget(self._campo_busqueda)

        layout.addStretch()

        # Contador
        self._lbl_contador = QLabel("0 mensajes")
        self._lbl_contador.setStyleSheet(
            f"color: {COLOR_TEXTO_SECUNDARIO}; font-size: 11px;"
        )
        layout.addWidget(self._lbl_contador)

        # Limpiar
        btn_limpiar = QPushButton("✖  Limpiar filtros")
        btn_limpiar.clicked.connect(self.limpiar)
        layout.addWidget(btn_limpiar)

    def _conectar_senales(self) -> None:
        self._date_desde.dateChanged.connect(self._emitir_cambio)
        self._date_hasta.dateChanged.connect(self._emitir_cambio)
        self._combo_remitente.currentTextChanged.connect(self._emitir_cambio)
        self._combo_equipo.currentTextChanged.connect(self._emitir_cambio)
        self._check_multimedia.stateChanged.connect(self._emitir_cambio)

        for chk in list(self._checks_tipo.values()) + list(self._checks_estado.values()):
            chk.stateChanged.connect(self._emitir_cambio)

        self._campo_busqueda.textChanged.connect(self._al_cambiar_busqueda)

    def _al_cambiar_busqueda(self, _texto: str) -> None:
        self._timer_busqueda.start(300)

    def _emitir_cambio(self) -> None:
        self.filtros_cambiados.emit()

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def limpiar(self) -> None:
        """Restablece todos los filtros."""
        self._date_desde.setDate(QDate(2020, 1, 1))
        self._date_hasta.setDate(QDate.currentDate())
        self._combo_remitente.setCurrentIndex(0)
        self._combo_equipo.setCurrentIndex(0)
        self._campo_busqueda.clear()
        self._check_multimedia.setChecked(False)
        for chk in self._checks_tipo.values():
            chk.setChecked(True)
        for chk in self._checks_estado.values():
            chk.setChecked(True)
        self._emitir_cambio()

    def set_remitentes(self, remitentes: list[str]) -> None:
        """Carga remitentes en el ComboBox."""
        actual = self._combo_remitente.currentText()
        self._combo_remitente.blockSignals(True)
        self._combo_remitente.clear()
        self._combo_remitente.addItem("Todos")
        for r in remitentes:
            self._combo_remitente.addItem(r)
        idx = self._combo_remitente.findText(actual)
        self._combo_remitente.setCurrentIndex(max(0, idx))
        self._combo_remitente.blockSignals(False)

    def set_equipos(self, equipos: list[str]) -> None:
        """Carga equipos en el ComboBox."""
        actual = self._combo_equipo.currentText()
        self._combo_equipo.blockSignals(True)
        self._combo_equipo.clear()
        self._combo_equipo.addItem("Todos")
        self._combo_equipo.addItem("Sin clasificar")
        for e in equipos:
            self._combo_equipo.addItem(e)
        idx = self._combo_equipo.findText(actual)
        self._combo_equipo.setCurrentIndex(max(0, idx))
        self._combo_equipo.blockSignals(False)

    def set_contador(self, texto: str) -> None:
        """Actualiza el texto del contador inferior."""
        self._lbl_contador.setText(texto)

    def filtros_actuales(self) -> dict:
        """Retorna un dict con los filtros actuales."""
        tipos = [k for k, v in self._checks_tipo.items() if v.isChecked()]
        estados = [k for k, v in self._checks_estado.items() if v.isChecked()]
        return {
            "fecha_desde": self._date_desde.date().toString("yyyy-MM-dd"),
            "fecha_hasta": self._date_hasta.date().toString("yyyy-MM-dd"),
            "remitente": self._combo_remitente.currentText(),
            "equipo": self._combo_equipo.currentText(),
            "tipos": tipos,
            "estados": estados,
            "solo_multimedia": self._check_multimedia.isChecked(),
            "keyword": self._campo_busqueda.text().strip(),
        }

    def _lbl_seccion(self, texto: str) -> QLabel:
        lbl = QLabel(texto.upper())
        lbl.setStyleSheet(
            f"color: {COLOR_TEXTO_SECUNDARIO}; font-size: 10px; "
            f"font-weight: 600; letter-spacing: 0.8px; margin-top: 4px;"
        )
        return lbl
