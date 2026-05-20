"""
ui/widgets/edit_dialog.py
-------------------------
Diálogo de edición de un mensaje.
"""

from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QGridLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from config import TIPOS_MENSAJE
from database.models import Mensaje
import database.repo_mensajes as repo_mensajes


class EditDialog(QDialog):
    """Diálogo modal para editar un mensaje."""

    def __init__(self, mensaje: Mensaje, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._mensaje = mensaje

        self.setWindowTitle(f"Editar mensaje ID {mensaje.id}")
        self.setMinimumWidth(720)

        self._construir_ui()
        self._cargar_datos()

    def _construir_ui(self) -> None:
        layout = QVBoxLayout(self)

        grupo = QGroupBox("Datos del mensaje")
        form = QGridLayout(grupo)

        self._campo_fecha = QLineEdit()
        self._campo_hora = QLineEdit()
        self._campo_remitente = QLineEdit()
        self._campo_equipo = QLineEdit()
        self._campo_tipo = QLineEdit()

        self._campo_texto = QTextEdit()
        self._campo_texto.setMinimumHeight(140)

        self._lista_adjuntos = QListWidget()
        self._lista_adjuntos.setMinimumHeight(80)

        self._campo_notas = QTextEdit()
        self._campo_notas.setPlaceholderText("Notas manuales (se agregan al final del texto)")
        self._campo_notas.setMinimumHeight(80)

        btn_add_adj = QPushButton("Agregar adjunto")
        btn_add_adj.clicked.connect(self._agregar_adjunto)
        btn_remove_adj = QPushButton("Quitar adjunto")
        btn_remove_adj.clicked.connect(self._quitar_adjunto)

        form.addWidget(QLabel("Fecha (YYYY-MM-DD):"), 0, 0)
        form.addWidget(self._campo_fecha, 0, 1)
        form.addWidget(QLabel("Hora (HH:MM):"), 0, 2)
        form.addWidget(self._campo_hora, 0, 3)

        form.addWidget(QLabel("Remitente:"), 1, 0)
        form.addWidget(self._campo_remitente, 1, 1, 1, 3)

        form.addWidget(QLabel("Equipo:"), 2, 0)
        form.addWidget(self._campo_equipo, 2, 1)
        form.addWidget(QLabel("Tipo:"), 2, 2)
        form.addWidget(self._campo_tipo, 2, 3)

        form.addWidget(QLabel("Texto:"), 3, 0)
        form.addWidget(self._campo_texto, 3, 1, 1, 3)

        form.addWidget(QLabel("Adjuntos:"), 4, 0)
        form.addWidget(self._lista_adjuntos, 4, 1, 1, 3)

        botones_adj = QVBoxLayout()
        botones_adj.addWidget(btn_add_adj)
        botones_adj.addWidget(btn_remove_adj)
        form.addLayout(botones_adj, 4, 4)

        form.addWidget(QLabel("Notas manuales:"), 5, 0)
        form.addWidget(self._campo_notas, 5, 1, 1, 3)

        layout.addWidget(grupo)

        botones = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        botones.accepted.connect(self._guardar)
        botones.rejected.connect(self.reject)
        layout.addWidget(botones)

    def _cargar_datos(self) -> None:
        self._campo_fecha.setText(self._mensaje.fecha)
        self._campo_hora.setText(self._mensaje.hora)
        self._campo_remitente.setText(self._mensaje.remitente)
        self._campo_equipo.setText(self._mensaje.equipo or "")
        self._campo_tipo.setText(self._mensaje.tipo_mensaje or "")
        self._campo_texto.setPlainText(self._mensaje.texto)
        self._lista_adjuntos.clear()
        for adj in self._mensaje.adjuntos:
            self._lista_adjuntos.addItem(adj)

    def _agregar_adjunto(self) -> None:
        from PyQt6.QtWidgets import QInputDialog
        nombre, ok = QInputDialog.getText(self, "Adjunto", "Nombre del archivo:")
        if ok and nombre:
            self._lista_adjuntos.addItem(nombre)

    def _quitar_adjunto(self) -> None:
        fila = self._lista_adjuntos.currentRow()
        if fila >= 0:
            self._lista_adjuntos.takeItem(fila)

    def _guardar(self) -> None:
        self._mensaje.fecha = self._campo_fecha.text().strip()
        self._mensaje.hora = self._campo_hora.text().strip()
        self._mensaje.remitente = self._campo_remitente.text().strip()
        self._mensaje.equipo = self._campo_equipo.text().strip() or None

        tipo = self._campo_tipo.text().strip()
        self._mensaje.tipo_mensaje = tipo if tipo in TIPOS_MENSAJE else (tipo or None)

        texto = self._campo_texto.toPlainText().strip()
        notas = self._campo_notas.toPlainText().strip()
        if notas:
            texto = f"{texto}\n\n[Nota manual]\n{notas}" if texto else notas
        self._mensaje.texto = texto

        self._mensaje.adjuntos = [
            self._lista_adjuntos.item(i).text()
            for i in range(self._lista_adjuntos.count())
        ]

        self._mensaje.editado_manual = True

        repo_mensajes.actualizar(self._mensaje)
        self.accept()

    @property
    def mensaje_actualizado(self) -> Mensaje:
        return self._mensaje
