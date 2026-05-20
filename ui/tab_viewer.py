"""
ui/tab_viewer.py
----------------
Tab del visor de mensajes con tabla y filtros completos.
"""

from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

import database.repo_mensajes as repo_mensajes
import database.repo_equipos as repo_equipos
from database.models import Mensaje
from config import ESTADOS_PROCESO, TIPOS_MENSAJE
from ui.styles import COLOR_TEXTO_SECUNDARIO
from ui.widgets.filter_panel import FilterPanel
from ui.widgets.message_table import MensajeTableView


class TabViewer(QWidget):
    """
    Tab de visualización, filtrado y edición de mensajes.

    Señales:
        solicitar_edicion(Mensaje):      Pide abrir EditDialog.
        solicitar_ver_adjuntos(Mensaje): Pide abrir MediaViewer.
    """

    solicitar_edicion       = pyqtSignal(object)
    solicitar_ver_adjuntos  = pyqtSignal(object)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._construir_ui()
        self._conectar_senales()

    # ------------------------------------------------------------------
    # Construcción de la interfaz
    # ------------------------------------------------------------------

    def _construir_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        splitter = QSplitter(Qt.Orientation.Horizontal, self)
        splitter.setHandleWidth(2)

        # Panel izquierdo de filtros (scrollable)
        self._filtros = FilterPanel(self)
        filtros_scroll = QScrollArea()
        filtros_scroll.setWidgetResizable(True)
        filtros_scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        filtros_scroll.setWidget(self._filtros)
        filtros_scroll.setMinimumWidth(260)
        splitter.addWidget(filtros_scroll)

        # Panel derecho: tabla + barra inferior
        panel_tabla = self._construir_panel_tabla()
        splitter.addWidget(panel_tabla)

        splitter.setSizes([280, 900])
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        layout.addWidget(splitter)

    def _construir_panel_tabla(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._tabla = MensajeTableView(self)
        layout.addWidget(self._tabla, stretch=1)

        barra_inferior = self._construir_barra_inferior()
        layout.addWidget(barra_inferior)

        return panel

    def _construir_barra_inferior(self) -> QWidget:
        barra = QWidget()
        barra.setFixedHeight(36)
        barra.setStyleSheet(
            "background-color: #1E2022; border-top: 1px solid #3A4040;"
        )

        layout = QHBoxLayout(barra)
        layout.setContentsMargins(12, 0, 12, 0)

        self._lbl_contador = QLabel("Cargando...")
        self._lbl_contador.setStyleSheet(
            f"color: {COLOR_TEXTO_SECUNDARIO}; font-size: 11px;"
        )
        layout.addWidget(self._lbl_contador)

        layout.addStretch()

        btn_recargar = QPushButton("↻  Actualizar")
        btn_recargar.setFixedHeight(26)
        btn_recargar.clicked.connect(self._recargar_todo)
        layout.addWidget(btn_recargar)

        return barra

    # ------------------------------------------------------------------
    # Señales
    # ------------------------------------------------------------------

    def _conectar_senales(self) -> None:
        self._filtros.filtros_cambiados.connect(self._recargar_tabla)
        self._tabla.modelo.solicitar_edicion.connect(
            lambda msg: self.solicitar_edicion.emit(msg)
        )
        self._tabla.modelo.solicitar_ver_adjuntos.connect(
            lambda msg: self.solicitar_ver_adjuntos.emit(msg)
        )
        self._tabla.solicitar_eliminar.connect(self._confirmar_eliminar)

    # ------------------------------------------------------------------
    # Carga de datos
    # ------------------------------------------------------------------

    def recargar(self) -> None:
        """Recarga filtros y tabla desde la BD."""
        self._recargar_listas_filtros()
        self._recargar_tabla()

    def _recargar_todo(self) -> None:
        self._recargar_listas_filtros()
        self._recargar_tabla()

    def _recargar_listas_filtros(self) -> None:
        try:
            remitentes = repo_mensajes.get_remitentes_unicos()
            self._filtros.set_remitentes(remitentes)
        except Exception:
            self._filtros.set_remitentes([])

        try:
            equipos = [e.nombre for e in repo_equipos.get_all(include_inactivos=True)]
            self._filtros.set_equipos(equipos)
        except Exception:
            self._filtros.set_equipos([])

    def _recargar_tabla(self) -> None:
        filtros = self._filtros.filtros_actuales()

        remitente = filtros["remitente"]
        equipo = filtros["equipo"]
        tipos = filtros["tipos"]
        estados = filtros["estados"]

        if len(tipos) == len(TIPOS_MENSAJE):
            tipos = None
        if len(estados) == len(ESTADOS_PROCESO):
            estados = None

        if tipos == [] or estados == []:
            self._tabla.cargar_mensajes([])
            total_bd = repo_mensajes.contar()
            texto = f"Mostrando 0 de {total_bd:,} mensajes"
            self._lbl_contador.setText(texto)
            self._filtros.set_contador(texto)
            return

        equipo_sin = equipo == "Sin clasificar"
        equipo_val = None if equipo in ("Todos", "Sin clasificar") else equipo

        try:
            mensajes = repo_mensajes.get_por_filtros(
                fecha_desde=filtros["fecha_desde"],
                fecha_hasta=filtros["fecha_hasta"],
                remitente=None if remitente == "Todos" else remitente,
                equipo=equipo_val,
                tipo_mensaje=tipos,
                estado_proceso=estados,
                equipo_sin_clasificar=equipo_sin,
                solo_con_multimedia=filtros["solo_multimedia"],
                keyword=filtros["keyword"] or None,
            )
        except Exception as exc:
            self._lbl_contador.setText(f"Error al cargar datos: {exc}")
            return

        self._tabla.cargar_mensajes(mensajes)

        total_bd = repo_mensajes.contar()
        mostrados = self._tabla.total()
        if mostrados == total_bd:
            texto = f"{total_bd:,} mensajes"
        else:
            texto = f"Mostrando {mostrados:,} de {total_bd:,} mensajes"
        self._lbl_contador.setText(texto)
        self._filtros.set_contador(texto)

    # ------------------------------------------------------------------
    # Eliminación de mensajes
    # ------------------------------------------------------------------

    def _confirmar_eliminar(self, mensajes: list[Mensaje]) -> None:
        n = len(mensajes)
        respuesta = QMessageBox.question(
            self,
            "Confirmar eliminación",
            f"¿Eliminar {'este mensaje' if n == 1 else f'estos {n} mensajes'}?\n\n"
            "Esta acción no se puede deshacer.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if respuesta != QMessageBox.StandardButton.Yes:
            return

        errores = []
        for msg in mensajes:
            if msg.id:
                try:
                    repo_mensajes.eliminar(msg.id)
                except Exception as exc:
                    errores.append(f"ID {msg.id}: {exc}")

        if errores:
            QMessageBox.warning(
                self,
                "Errores al eliminar",
                f"No se pudieron eliminar {len(errores)} mensaje(s):\n"
                + "\n".join(errores[:5]),
            )

        self._recargar_tabla()

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def actualizar_mensaje_en_tabla(self, mensaje: Mensaje) -> None:
        self._tabla.actualizar_mensaje(mensaje)
        total_bd = repo_mensajes.contar()
        self._lbl_contador.setText(
            f"Mostrando {self._tabla.total():,} de {total_bd:,} mensajes"
        )

    def mensajes_visibles(self) -> list[Mensaje]:
        """Retorna los mensajes actualmente cargados en la tabla."""
        return self._tabla.mensajes()
