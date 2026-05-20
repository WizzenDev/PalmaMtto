"""
ui/widgets/media_viewer.py
--------------------------
Visor de multimedia para adjuntos de un mensaje.
"""

import os
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from config import EXTENSIONES_IMAGEN
from database.connection import db
from database.models import Mensaje


def _obtener_directorio_multimedia() -> Optional[Path]:
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT valor FROM configuracion WHERE clave = 'directorio_multimedia'"
    )
    row = cursor.fetchone()
    if row and row[0]:
        return Path(row[0])
    return None


class MediaViewer(QDialog):
    """Diálogo para visualizar adjuntos del mensaje."""

    def __init__(self, mensaje: Mensaje, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._mensaje = mensaje
        self._index = 0
        self._directorio = _obtener_directorio_multimedia()

        self.setWindowTitle("Adjuntos del mensaje")
        self.setMinimumSize(720, 520)

        self._construir_ui()
        self._mostrar_actual()

    def _construir_ui(self) -> None:
        layout = QVBoxLayout(self)

        self._lbl_info = QLabel("")
        self._lbl_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._lbl_info)

        self._preview = QLabel("Sin vista previa")
        self._preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._preview.setMinimumHeight(320)
        self._preview.setStyleSheet("border: 1px solid #3A4040;")
        layout.addWidget(self._preview, stretch=1)

        fila_botones = QHBoxLayout()
        self._btn_prev = QPushButton("◀ Anterior")
        self._btn_next = QPushButton("Siguiente ▶")
        self._btn_abrir = QPushButton("Abrir archivo")
        self._btn_prev.clicked.connect(self._anterior)
        self._btn_next.clicked.connect(self._siguiente)
        self._btn_abrir.clicked.connect(self._abrir_archivo)

        fila_botones.addWidget(self._btn_prev)
        fila_botones.addWidget(self._btn_next)
        fila_botones.addStretch()
        fila_botones.addWidget(self._btn_abrir)
        layout.addLayout(fila_botones)

    def _mostrar_actual(self) -> None:
        if not self._mensaje.adjuntos:
            if self._mensaje.media_omitida:
                self._preview.setText(
                    "Este archivo no fue exportado desde WhatsApp (media omitted)"
                )
            else:
                self._preview.setText("Sin adjuntos para mostrar")
            self._btn_prev.setEnabled(False)
            self._btn_next.setEnabled(False)
            self._btn_abrir.setEnabled(False)
            return

        nombre = self._mensaje.adjuntos[self._index]
        self._lbl_info.setText(f"{self._index + 1} / {len(self._mensaje.adjuntos)} — {nombre}")

        if not self._directorio:
            self._preview.setText("Directorio de multimedia no configurado")
            self._btn_abrir.setEnabled(False)
            return

        ruta = self._directorio / nombre
        if not ruta.exists():
            self._preview.setText(f"Archivo no encontrado en:\n{ruta}")
            self._btn_abrir.setEnabled(False)
            return

        self._btn_abrir.setEnabled(True)

        if ruta.suffix.lower() in EXTENSIONES_IMAGEN:
            pixmap = QPixmap(str(ruta))
            if pixmap.isNull():
                self._preview.setText("No se pudo cargar la imagen")
            else:
                self._preview.setPixmap(pixmap.scaled(
                    self._preview.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                ))
        else:
            self._preview.setText("Vista previa no disponible para este archivo")

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        super().resizeEvent(event)
        self._mostrar_actual()

    def _anterior(self) -> None:
        if self._index > 0:
            self._index -= 1
            self._mostrar_actual()

    def _siguiente(self) -> None:
        if self._index < len(self._mensaje.adjuntos) - 1:
            self._index += 1
            self._mostrar_actual()

    def _abrir_archivo(self) -> None:
        if not self._directorio or not self._mensaje.adjuntos:
            return
        ruta = self._directorio / self._mensaje.adjuntos[self._index]
        if not ruta.exists():
            QMessageBox.warning(self, "Archivo no encontrado", str(ruta))
            return
        os.startfile(str(ruta))
