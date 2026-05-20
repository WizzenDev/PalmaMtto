"""
ui/widgets/batch_panel.py
-------------------------
Panel de control y tabla de lotes.
"""

from typing import Optional

from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


class BatchPanel(QWidget):
    """Panel con tabla de lotes y botones de accion."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._construir_ui()

    def _construir_ui(self) -> None:
        layout = QVBoxLayout(self)

        self.tabla = QTableWidget(0, 6)
        self.tabla.setHorizontalHeaderLabels(
            ["# Lote", "Rango", "Cantidad", "Estado", "Tokens", "Fecha"]
        )
        self.tabla.horizontalHeader().setStretchLastSection(True)
        self.tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.tabla, stretch=1)

        fila = QHBoxLayout()
        self.btn_procesar = QPushButton("Procesar lote")
        self.btn_procesar_sel = QPushButton("Procesar seleccion")
        self.btn_procesar_todos = QPushButton("Procesar pendientes")
        self.btn_reprocesar = QPushButton("Reprocesar error")
        self.lbl_progreso = QLabel("0 / 0")

        fila.addWidget(self.btn_procesar)
        fila.addWidget(self.btn_procesar_sel)
        fila.addWidget(self.btn_procesar_todos)
        fila.addWidget(self.btn_reprocesar)
        fila.addStretch()
        fila.addWidget(self.lbl_progreso)
        layout.addLayout(fila)
