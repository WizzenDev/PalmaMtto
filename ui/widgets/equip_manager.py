"""
ui/widgets/equip_manager.py
---------------------------
Diálogo de gestión de equipos.
"""

from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from database.models import Equipo
import database.repo_equipos as repo_equipos


class EquipManager(QDialog):
    """Diálogo para administrar equipos."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Gestión de equipos")
        self.setMinimumSize(640, 420)

        self._construir_ui()
        self._recargar_tabla()

    def _construir_ui(self) -> None:
        layout = QVBoxLayout(self)

        self._tabla = QTableWidget(0, 4)
        self._tabla.setHorizontalHeaderLabels(
            ["Nombre", "Descripción", "Origen", "Activo"]
        )
        self._tabla.horizontalHeader().setStretchLastSection(True)
        self._tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self._tabla, stretch=1)

        fila_botones = QHBoxLayout()
        btn_agregar = QPushButton("Agregar")
        btn_editar = QPushButton("Editar")
        btn_toggle = QPushButton("Activar/Desactivar")
        btn_eliminar = QPushButton("Eliminar")
        btn_fusionar = QPushButton("Fusionar")

        btn_agregar.clicked.connect(self._agregar)
        btn_editar.clicked.connect(self._editar)
        btn_toggle.clicked.connect(self._toggle)
        btn_eliminar.clicked.connect(self._eliminar)
        btn_fusionar.clicked.connect(self._fusionar)

        fila_botones.addWidget(btn_agregar)
        fila_botones.addWidget(btn_editar)
        fila_botones.addWidget(btn_toggle)
        fila_botones.addWidget(btn_eliminar)
        fila_botones.addWidget(btn_fusionar)
        fila_botones.addStretch()

        layout.addLayout(fila_botones)

        botones = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        botones.rejected.connect(self.reject)
        layout.addWidget(botones)

    def _recargar_tabla(self) -> None:
        equipos = repo_equipos.get_all(include_inactivos=True)
        self._tabla.setRowCount(0)
        for eq in equipos:
            row = self._tabla.rowCount()
            self._tabla.insertRow(row)
            self._tabla.setItem(row, 0, QTableWidgetItem(eq.nombre))
            self._tabla.setItem(row, 1, QTableWidgetItem(eq.descripcion or ""))
            self._tabla.setItem(row, 2, QTableWidgetItem(eq.origen))
            item_activo = QTableWidgetItem("Sí" if eq.activo else "No")
            item_activo.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._tabla.setItem(row, 3, item_activo)
            self._tabla.setRowHeight(row, 24)
            self._tabla.item(row, 0).setData(Qt.ItemDataRole.UserRole, eq)

    def _equipo_seleccionado(self) -> Optional[Equipo]:
        fila = self._tabla.currentRow()
        if fila < 0:
            return None
        item = self._tabla.item(fila, 0)
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def _agregar(self) -> None:
        dlg = _EquipoDialog(self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        equipo = dlg.obtener_equipo()
        repo_equipos.insertar(equipo)
        self._recargar_tabla()

    def _editar(self) -> None:
        equipo = self._equipo_seleccionado()
        if not equipo:
            return
        dlg = _EquipoDialog(self, equipo)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        actualizado = dlg.obtener_equipo()
        actualizado.id = equipo.id
        if actualizado.nombre != equipo.nombre:
            repo_equipos.renombrar(equipo.id, actualizado.nombre)
            actualizado.nombre = actualizado.nombre
        repo_equipos.actualizar(actualizado)
        self._recargar_tabla()

    def _toggle(self) -> None:
        equipo = self._equipo_seleccionado()
        if not equipo:
            return
        repo_equipos.activar(equipo.id, not equipo.activo)
        self._recargar_tabla()

    def _eliminar(self) -> None:
        equipo = self._equipo_seleccionado()
        if not equipo:
            return
        uso = repo_equipos.contar_mensajes_por_equipo(equipo.nombre)
        if uso > 0:
            QMessageBox.warning(
                self,
                "No se puede eliminar",
                f"El equipo está asignado a {uso} mensaje(s).",
            )
            return
        if QMessageBox.question(
            self,
            "Eliminar equipo",
            f"¿Eliminar '{equipo.nombre}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        ) == QMessageBox.StandardButton.Yes:
            repo_equipos.eliminar(equipo.id)
            self._recargar_tabla()

    def _fusionar(self) -> None:
        equipo = self._equipo_seleccionado()
        if not equipo:
            return
        from PyQt6.QtWidgets import QInputDialog
        destino, ok = QInputDialog.getText(
            self,
            "Fusionar equipo",
            "Nombre del equipo destino:",
        )
        if not ok or not destino:
            return
        if destino == equipo.nombre:
            return
        repo_equipos.fusionar(equipo.nombre, destino)
        self._recargar_tabla()


class _EquipoDialog(QDialog):
    """Diálogo para crear/editar un equipo."""

    def __init__(self, parent: Optional[QWidget] = None, equipo: Optional[Equipo] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Equipo")
        self._equipo = equipo

        layout = QVBoxLayout(self)
        form = QGridLayout()

        self._campo_nombre = QLineEdit()
        self._campo_desc = QLineEdit()
        self._check_activo = QCheckBox("Activo")
        self._check_activo.setChecked(True)

        form.addWidget(QLabel("Nombre:"), 0, 0)
        form.addWidget(self._campo_nombre, 0, 1)
        form.addWidget(QLabel("Descripción:"), 1, 0)
        form.addWidget(self._campo_desc, 1, 1)
        form.addWidget(self._check_activo, 2, 1)

        layout.addLayout(form)

        botones = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        botones.accepted.connect(self.accept)
        botones.rejected.connect(self.reject)
        layout.addWidget(botones)

        if equipo:
            self._campo_nombre.setText(equipo.nombre)
            self._campo_desc.setText(equipo.descripcion or "")
            self._check_activo.setChecked(equipo.activo)

    def obtener_equipo(self) -> Equipo:
        return Equipo(
            nombre=self._campo_nombre.text().strip(),
            descripcion=self._campo_desc.text().strip() or None,
            activo=self._check_activo.isChecked(),
            origen="manual",
        )
