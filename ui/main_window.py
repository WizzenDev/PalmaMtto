"""
ui/main_window.py
-----------------
Ventana principal de PalmaMtto Desktop.

Contiene el QTabWidget con las 4 tabs de la aplicación y el menú principal.
Gestiona el ciclo de vida de la conexión a la BD y coordina la comunicación
entre tabs mediante señales.

Decisión de diseño: la ventana principal actúa como coordinador (mediator)
entre tabs. No contiene lógica de negocio propia; delega todo a los tabs y
repositorios. Las tabs se crean perezosamente (solo al construir la ventana)
y permanecen vivas durante toda la sesión.
"""

from typing import Optional

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QAction, QCloseEvent
from PyQt6.QtWidgets import (
    QLabel,
    QMainWindow,
    QMessageBox,
    QStatusBar,
    QTabWidget,
    QWidget,
)

from config import APP_NAME, APP_VERSION
from database.connection import db
from database.models import Mensaje


class MainWindow(QMainWindow):
    """
    Ventana principal de PalmaMtto Desktop.

    Estructura:
        MenuBar         → Archivo, Ver, Ayuda
        QTabWidget      → Tab Parseo | Tab Visor | Tab IA | Tab Config
        QStatusBar      → Información contextual
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        self._construir_ventana()
        self._construir_menu()
        self._construir_statusbar()
        self._construir_tabs()
        self._conectar_senales()

        # Carga inicial de la tabla de mensajes al arrancar
        self._tab_visor.recargar()
        self._actualizar_statusbar()

    # ------------------------------------------------------------------
    # Construcción de la UI
    # ------------------------------------------------------------------

    def _construir_ventana(self) -> None:
        """Configura propiedades básicas de la ventana."""
        self.setWindowTitle(f"{APP_NAME}  v{APP_VERSION}")
        self.setMinimumSize(QSize(1024, 680))
        self.resize(1280, 800)

    def _construir_menu(self) -> None:
        """Construye la barra de menú con acciones principales."""
        menubar = self.menuBar()

        # ── Menú Archivo ──────────────────────────────────────────────
        menu_archivo = menubar.addMenu("Archivo")

        accion_abrir = QAction("Cargar chat de WhatsApp...", self)
        accion_abrir.setShortcut("Ctrl+O")
        accion_abrir.setStatusTip("Abrir un archivo .txt exportado de WhatsApp")
        accion_abrir.triggered.connect(self._ir_a_tab_parseo)
        menu_archivo.addAction(accion_abrir)

        menu_archivo.addSeparator()

        # Submenú Exportar
        menu_exportar = menu_archivo.addMenu("Exportar...")
        accion_csv = QAction("Como CSV...", self)
        accion_csv.triggered.connect(self._exportar_csv)
        menu_exportar.addAction(accion_csv)

        accion_excel = QAction("Como Excel (.xlsx)...", self)
        accion_excel.triggered.connect(self._exportar_excel)
        menu_exportar.addAction(accion_excel)

        accion_json = QAction("Como JSON...", self)
        accion_json.triggered.connect(self._exportar_json)
        menu_exportar.addAction(accion_json)

        menu_archivo.addSeparator()

        accion_salir = QAction("Salir", self)
        accion_salir.setShortcut("Ctrl+Q")
        accion_salir.triggered.connect(self.close)
        menu_archivo.addAction(accion_salir)

        # ── Menú Ver ──────────────────────────────────────────────────
        menu_ver = menubar.addMenu("Ver")

        accion_parseo = QAction("Tab: Parseo", self)
        accion_parseo.setShortcut("Ctrl+1")
        accion_parseo.triggered.connect(lambda: self._tabs.setCurrentIndex(0))
        menu_ver.addAction(accion_parseo)

        accion_visor = QAction("Tab: Visor de mensajes", self)
        accion_visor.setShortcut("Ctrl+2")
        accion_visor.triggered.connect(lambda: self._tabs.setCurrentIndex(1))
        menu_ver.addAction(accion_visor)

        accion_ia = QAction("Tab: Procesamiento IA", self)
        accion_ia.setShortcut("Ctrl+3")
        accion_ia.triggered.connect(lambda: self._tabs.setCurrentIndex(2))
        menu_ver.addAction(accion_ia)

        accion_config = QAction("Tab: Configuración", self)
        accion_config.setShortcut("Ctrl+4")
        accion_config.triggered.connect(lambda: self._tabs.setCurrentIndex(3))
        menu_ver.addAction(accion_config)

        menu_ver.addSeparator()

        accion_actualizar = QAction("Actualizar tabla", self)
        accion_actualizar.setShortcut("F5")
        accion_actualizar.triggered.connect(self._recargar_visor)
        menu_ver.addAction(accion_actualizar)

        # ── Menú Herramientas ─────────────────────────────────────────
        menu_herr = menubar.addMenu("Herramientas")

        accion_equipos = QAction("Gestionar equipos...", self)
        accion_equipos.triggered.connect(self._abrir_gestor_equipos)
        menu_herr.addAction(accion_equipos)

        # ── Menú Ayuda ────────────────────────────────────────────────
        menu_ayuda = menubar.addMenu("Ayuda")

        accion_acerca = QAction(f"Acerca de {APP_NAME}...", self)
        accion_acerca.triggered.connect(self._mostrar_acerca_de)
        menu_ayuda.addAction(accion_acerca)

    def _construir_statusbar(self) -> None:
        """Construye la barra de estado inferior."""
        self._statusbar = QStatusBar()
        self.setStatusBar(self._statusbar)

        # Label permanente para info de BD
        self._lbl_status_bd = QLabel()
        self._statusbar.addPermanentWidget(self._lbl_status_bd)

        self._statusbar.showMessage("Listo")

    def _construir_tabs(self) -> None:
        """Crea el QTabWidget y los 4 tabs de la aplicación."""
        self._tabs = QTabWidget()
        self._tabs.setDocumentMode(False)
        self.setCentralWidget(self._tabs)

        # ── Tab 0: Parseo ─────────────────────────────────────────────
        from ui.tab_parser import TabParser
        self._tab_parseo = TabParser(self)
        self._tabs.addTab(self._tab_parseo, "📂  Parseo")

        # ── Tab 1: Visor ──────────────────────────────────────────────
        from ui.tab_viewer import TabViewer
        self._tab_visor = TabViewer(self)
        self._tabs.addTab(self._tab_visor, "📋  Mensajes")

        # ── Tab 2: IA ───────────────────────────────────────────────
        from ui.tab_ai import TabAI
        self._tab_ia = TabAI(self)
        self._tabs.addTab(self._tab_ia, "🤖  IA")

        # ── Tab 3: Configuración ─────────────────────────────────────
        from ui.tab_config import TabConfig
        self._tab_config = TabConfig(self)
        self._tabs.addTab(self._tab_config, "⚙️  Config")

    def _crear_tab_placeholder(self, titulo: str, descripcion: str) -> QWidget:
        """
        Crea un widget de placeholder para tabs aún no implementados.

        Args:
            titulo:      Título grande centrado.
            descripcion: Texto descriptivo de qué habrá en ese tab.

        Returns:
            QWidget listo para agregar al QTabWidget.
        """
        from PyQt6.QtWidgets import QVBoxLayout
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lbl_titulo = QLabel(titulo)
        lbl_titulo.setStyleSheet(
            "color: #5A8A3C; font-size: 22px; font-weight: 700;"
        )
        lbl_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lbl_desc = QLabel(descripcion)
        lbl_desc.setStyleSheet(
            "color: #9EA8A0; font-size: 13px; line-height: 1.6;"
        )
        lbl_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_desc.setWordWrap(True)

        layout.addWidget(lbl_titulo)
        layout.addSpacing(12)
        layout.addWidget(lbl_desc)

        return widget

    # ------------------------------------------------------------------
    # Conexión de señales entre tabs
    # ------------------------------------------------------------------

    def _conectar_senales(self) -> None:
        """Conecta señales entre tabs y la ventana principal."""
        # Cuando el parser termina → recargar el visor y saltar a él
        self._tab_parseo.parseo_completado.connect(self._al_parseo_completado)

        # Señales del visor hacia diálogos (implementados en Etapa 3)
        self._tab_visor.solicitar_edicion.connect(self._al_solicitar_edicion)
        self._tab_visor.solicitar_ver_adjuntos.connect(self._al_solicitar_ver_adjuntos)

        # Actualizar statusbar al cambiar de tab
        self._tabs.currentChanged.connect(self._al_cambiar_tab)

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _al_parseo_completado(self) -> None:
        """Recarga el visor y salta a él cuando el parser termina."""
        self._tab_visor.recargar()
        self._tabs.setCurrentIndex(1)   # Saltar al visor
        self._actualizar_statusbar()
        self._statusbar.showMessage("Carga completada. Datos disponibles en el visor.", 5000)

    def _al_solicitar_edicion(self, mensaje: Mensaje) -> None:
        """
        Abre el diálogo de edición de un mensaje.

        En Etapa 3 abre EditDialog.
        """
        from ui.widgets.edit_dialog import EditDialog
        dlg = EditDialog(mensaje, self)
        if dlg.exec() == dlg.DialogCode.Accepted:
            self._tab_visor.actualizar_mensaje_en_tabla(dlg.mensaje_actualizado)

    def _al_solicitar_ver_adjuntos(self, mensaje: Mensaje) -> None:
        """
        Abre el visor de multimedia.

        En Etapa 3 abre MediaViewer.
        """
        from ui.widgets.media_viewer import MediaViewer
        dlg = MediaViewer(mensaje, self)
        dlg.exec()

    def _al_cambiar_tab(self, indice: int) -> None:
        """Actualiza el statusbar al cambiar de tab."""
        nombres = ["Parseo", "Visor de mensajes", "Procesamiento IA", "Configuración"]
        if 0 <= indice < len(nombres):
            self._statusbar.showMessage(f"Tab: {nombres[indice]}")

    def _ir_a_tab_parseo(self) -> None:
        """Salta al tab de parseo (acción del menú Archivo)."""
        self._tabs.setCurrentIndex(0)

    def _recargar_visor(self) -> None:
        """Recarga el visor desde la BD (atajo F5)."""
        self._tab_visor.recargar()
        self._actualizar_statusbar()

    def _mostrar_acerca_de(self) -> None:
        """Muestra el diálogo Acerca de."""
        from config import DB_PATH
        QMessageBox.about(
            self,
            f"Acerca de {APP_NAME}",
            f"<b>{APP_NAME}</b> v{APP_VERSION}<br><br>"
            f"Herramienta de gestión de mantenimiento para<br>"
            f"plantas extractoras de aceite de palma.<br><br>"
            f"<b>Stack:</b> Python 3.11+ · PyQt6 · SQLite<br><br>"
            f"<b>Base de datos:</b><br>{DB_PATH}",
        )

    def _abrir_gestor_equipos(self) -> None:
        """Abre el gestor de equipos."""
        from ui.widgets.equip_manager import EquipManager
        dlg = EquipManager(self)
        dlg.exec()
        self._tab_visor.recargar()

    def _exportar_csv(self) -> None:
        self._exportar("csv")

    def _exportar_excel(self) -> None:
        self._exportar("xlsx")

    def _exportar_json(self) -> None:
        self._exportar("json")

    def _exportar(self, formato: str) -> None:
        """Exporta los mensajes visibles en el visor."""
        from pathlib import Path
        from PyQt6.QtWidgets import QFileDialog

        filtros = "CSV (*.csv)" if formato == "csv" else (
            "Excel (*.xlsx)" if formato == "xlsx" else "JSON (*.json)"
        )
        ruta, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar mensajes",
            "",
            filtros,
        )
        if not ruta:
            return

        mensajes = self._tab_visor.mensajes_visibles()
        ruta_path = Path(ruta)

        if formato == "csv":
            from export.csv_exporter import exportar_csv
            exportar_csv(mensajes, ruta_path)
        elif formato == "xlsx":
            from export.excel_exporter import exportar_excel
            exportar_excel(mensajes, ruta_path)
        else:
            from export.json_exporter import exportar_json
            exportar_json(mensajes, ruta_path)

        QMessageBox.information(
            self,
            "Exportación finalizada",
            f"Archivo exportado:\n{ruta_path}",
        )

    # ------------------------------------------------------------------
    # Utilidades
    # ------------------------------------------------------------------

    def _actualizar_statusbar(self) -> None:
        """Actualiza el label permanente de la barra de estado con el total en BD."""
        try:
            import database.repo_mensajes as repo_mensajes
            total = repo_mensajes.contar()
            self._lbl_status_bd.setText(f"  BD: {total:,} mensajes  ")
        except Exception:
            self._lbl_status_bd.setText("  BD: —  ")

    # ------------------------------------------------------------------
    # Ciclo de vida
    # ------------------------------------------------------------------

    def closeEvent(self, event: QCloseEvent) -> None:
        """Cierra la conexión a SQLite al salir de la aplicación."""
        db.close()
        event.accept()


# ---------------------------------------------------------------------------
# Siguiente archivo a construir: main.py (actualizar para Etapa 2 con PyQt6)
# ---------------------------------------------------------------------------
