"""
ui/tab_ai.py
------------
Tab de procesamiento IA por lotes (OpenAI).
"""

from typing import Optional

from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QSpinBox,
    QPushButton,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ai.batch_manager import BatchManager
import database.repo_config as repo_config
from ui.widgets.batch_panel import BatchPanel


class _Worker(QThread):
    progreso = pyqtSignal(int, int)
    terminado = pyqtSignal()

    def __init__(self, lotes: list[list[int]], parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._lotes = lotes
        self._manager = BatchManager()

    def run(self) -> None:
        self._manager.procesar_lotes(self._lotes, on_progress=self._emitir)
        self.terminado.emit()

    def _emitir(self, actual: int, total: int) -> None:
        self.progreso.emit(actual, total)


class TabAI(QWidget):
    """Tab de procesamiento por lotes."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._worker: Optional[_Worker] = None
        self._manager = BatchManager()
        self._construir_ui()
        self._cargar_lotes()

    def _construir_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Configuracion de envio
        grupo = QGroupBox("Configuracion de envio")
        fila = QHBoxLayout(grupo)

        self._spin_tamano = QSpinBox()
        self._spin_tamano.setRange(10, 200)
        self._spin_tamano.setValue(repo_config.get_int("tamano_lote", 50))
        self._spin_pausa = QSpinBox()
        self._spin_pausa.setRange(0, 10)
        self._spin_pausa.setValue(repo_config.get_int("pausa_entre_lotes", 1))

        btn_guardar = QPushButton("Guardar")
        btn_guardar.clicked.connect(self._guardar_config)

        fila.addWidget(QLabel("Tamano lote:"))
        fila.addWidget(self._spin_tamano)
        fila.addSpacing(12)
        fila.addWidget(QLabel("Pausa (s):"))
        fila.addWidget(self._spin_pausa)
        fila.addSpacing(12)
        fila.addWidget(btn_guardar)
        fila.addStretch()

        layout.addWidget(grupo)

        # Tabla de lotes
        self._panel = BatchPanel(self)
        self._panel.btn_procesar.clicked.connect(self._procesar_seleccionado)
        self._panel.btn_procesar_sel.clicked.connect(self._procesar_seleccion)
        self._panel.btn_procesar_todos.clicked.connect(self._procesar_pendientes)
        self._panel.btn_reprocesar.clicked.connect(self._procesar_seleccion)
        layout.addWidget(self._panel, stretch=1)

    def _guardar_config(self) -> None:
        repo_config.set_value("tamano_lote", str(self._spin_tamano.value()))
        repo_config.set_value("pausa_entre_lotes", str(self._spin_pausa.value()))
        self._manager = BatchManager()
        self._cargar_lotes()

    def _cargar_lotes(self) -> None:
        lotes = self._manager.generar_lotes()
        tabla = self._panel.tabla
        tabla.setRowCount(0)
        for idx, lote in enumerate(lotes, start=1):
            row = tabla.rowCount()
            tabla.insertRow(row)
            rango = f"{lote[0]}-{lote[-1]}" if lote else "-"
            tabla.setItem(row, 0, QTableWidgetItem(str(idx)))
            tabla.setItem(row, 1, QTableWidgetItem(rango))
            tabla.setItem(row, 2, QTableWidgetItem(str(len(lote))))
            tabla.setItem(row, 3, QTableWidgetItem("pendiente"))
            tabla.setItem(row, 4, QTableWidgetItem(""))
            tabla.setItem(row, 5, QTableWidgetItem(""))
            tabla.item(row, 0).setData(0x0100, lote)

        self._panel.lbl_progreso.setText(f"0 / {len(lotes)}")

    def _obtener_lotes_seleccionados(self) -> list[list[int]]:
        lotes: list[list[int]] = []
        for idx in self._panel.tabla.selectionModel().selectedRows():
            item = self._panel.tabla.item(idx.row(), 0)
            lote = item.data(0x0100) if item else None
            if lote:
                lotes.append(lote)
        return lotes

    def _procesar_seleccionado(self) -> None:
        lotes = self._obtener_lotes_seleccionados()
        if lotes:
            self._procesar(lotes[:1])

    def _procesar_seleccion(self) -> None:
        lotes = self._obtener_lotes_seleccionados()
        if lotes:
            self._procesar(lotes)

    def _procesar_pendientes(self) -> None:
        lotes = self._manager.generar_lotes()
        if lotes:
            self._procesar(lotes)

    def _procesar(self, lotes: list[list[int]]) -> None:
        if self._worker and self._worker.isRunning():
            return
        self._worker = _Worker(lotes, self)
        self._worker.progreso.connect(self._actualizar_progreso)
        self._worker.terminado.connect(self._cargar_lotes)
        self._worker.start()

    def _actualizar_progreso(self, actual: int, total: int) -> None:
        self._panel.lbl_progreso.setText(f"{actual} / {total}")
