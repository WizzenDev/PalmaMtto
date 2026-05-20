"""
ui/tab_parser.py
----------------
Tab de carga y parseo del archivo .txt exportado de WhatsApp.

El parseo se ejecuta en un QThread separado (HiloParseo) para no bloquear
la interfaz durante archivos de miles de líneas. La UI permanece responsiva
y muestra progreso en tiempo real.

Decisión de diseño: el hilo emite señales para actualizar la barra de progreso
y el log. No accede a widgets directamente desde el hilo (viola las reglas de
Qt con GUI); toda la actualización visual ocurre en el hilo principal a través
de las señales.
"""

from pathlib import Path
from typing import Optional

from PyQt6.QtCore import QThread, Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

import database.repo_mensajes as repo_mensajes
from parser.whatsapp_parser import ResumenParseo, parsear_archivo
from ui.styles import (
    COLOR_ACENTO_CLARO,
    COLOR_ERROR_TXT,
    COLOR_PROCESADO_TXT,
    COLOR_SIN_PROCESAR_TXT,
    COLOR_TEXTO_SECUNDARIO,
)


# ---------------------------------------------------------------------------
# Hilo de parseo
# ---------------------------------------------------------------------------

class HiloParseo(QThread):
    """
    Ejecuta parsear_archivo() en un hilo de fondo.

    Señales:
        progreso(actual, total):    Actualiza la barra de progreso.
        log(texto):                 Agrega una línea al área de log.
        terminado(ResumenParseo):   Parseo completado con éxito.
        error(str):                 Parseo terminó con excepción.
    """

    progreso  = pyqtSignal(int, int)      # (lineas_procesadas, total_lineas)
    log       = pyqtSignal(str)           # Mensaje de log
    terminado = pyqtSignal(object)        # ResumenParseo
    error     = pyqtSignal(str)           # Descripción del error

    def __init__(
        self,
        ruta: Path,
        reemplazar: bool,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._ruta = ruta
        self._reemplazar = reemplazar

    def run(self) -> None:
        """Ejecuta el parseo. Llamado automáticamente por QThread.start()."""
        try:
            import inspect
            sig = inspect.signature(parsear_archivo)
            kwargs: dict = dict(
                ruta_archivo=self._ruta,
                reemplazar=self._reemplazar,
                callback_progreso=self._callback_progreso,
            )
            # callback_log es una extensión de Etapa 2; el parser de Etapa 1
            # no lo tiene. Se agrega solo si la firma lo acepta.
            if "callback_log" in sig.parameters:
                kwargs["callback_log"] = self._callback_log

            resumen = parsear_archivo(**kwargs)
            self.terminado.emit(resumen)
        except Exception as exc:
            self.error.emit(str(exc))

    def _callback_progreso(self, actual: int, total: int) -> None:
        """Emite la señal de progreso desde el hilo de fondo."""
        self.progreso.emit(actual, total)

    def _callback_log(self, texto: str) -> None:
        """Emite la señal de log desde el hilo de fondo."""
        self.log.emit(texto)


# ---------------------------------------------------------------------------
# Widget del Tab Parseo
# ---------------------------------------------------------------------------

class TabParser(QWidget):
    """
    Tab de carga y parseo del archivo .txt de WhatsApp.

    Señales:
        parseo_completado(): Notifica a tab_viewer que recargue la tabla.
    """

    # Señal para avisar al resto de la app que hay datos nuevos
    parseo_completado = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        self._ruta_seleccionada: Optional[Path] = None
        self._hilo: Optional[HiloParseo] = None

        self._construir_ui()

    # ------------------------------------------------------------------
    # Construcción de la interfaz
    # ------------------------------------------------------------------

    def _construir_ui(self) -> None:
        """Construye todos los widgets del tab."""
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(16, 16, 16, 16)
        layout_principal.setSpacing(12)

        # --- Sección: Selección de archivo ---
        grupo_archivo = QGroupBox("Archivo de WhatsApp")
        layout_archivo = QVBoxLayout(grupo_archivo)
        layout_archivo.setSpacing(8)

        # Fila: campo de ruta + botón explorar
        fila_ruta = QHBoxLayout()
        self._lbl_ruta = QLabel("Ningún archivo seleccionado")
        self._lbl_ruta.setStyleSheet(f"color: {COLOR_TEXTO_SECUNDARIO}; font-style: italic;")
        self._lbl_ruta.setWordWrap(True)

        self._btn_seleccionar = QPushButton("📂  Seleccionar archivo .txt")
        self._btn_seleccionar.setMinimumWidth(200)
        self._btn_seleccionar.clicked.connect(self._seleccionar_archivo)

        fila_ruta.addWidget(self._lbl_ruta, stretch=1)
        fila_ruta.addWidget(self._btn_seleccionar)
        layout_archivo.addLayout(fila_ruta)

        # Fila: info del archivo seleccionado
        self._lbl_info_archivo = QLabel("")
        self._lbl_info_archivo.setStyleSheet(f"color: {COLOR_TEXTO_SECUNDARIO}; font-size: 11px;")
        layout_archivo.addWidget(self._lbl_info_archivo)

        layout_principal.addWidget(grupo_archivo)

        # --- Sección: Opciones de carga ---
        grupo_opciones = QGroupBox("Opciones de carga")
        layout_opciones = QHBoxLayout(grupo_opciones)

        self._btn_cargar = QPushButton("▶  Cargar y procesar")
        self._btn_cargar.setProperty("class", "primario")
        self._btn_cargar.setMinimumHeight(36)
        self._btn_cargar.setEnabled(False)
        self._btn_cargar.clicked.connect(self._iniciar_parseo)

        self._btn_cancelar = QPushButton("⏹  Cancelar")
        self._btn_cancelar.setEnabled(False)
        self._btn_cancelar.clicked.connect(self._cancelar_parseo)

        # Nota informativa
        lbl_nota = QLabel(
            "Si ya hay mensajes cargados, se preguntará si desea agregar o reemplazar."
        )
        lbl_nota.setStyleSheet(f"color: {COLOR_TEXTO_SECUNDARIO}; font-size: 11px;")
        lbl_nota.setWordWrap(True)

        layout_opciones.addWidget(self._btn_cargar)
        layout_opciones.addWidget(self._btn_cancelar)
        layout_opciones.addSpacing(16)
        layout_opciones.addWidget(lbl_nota, stretch=1)

        layout_principal.addWidget(grupo_opciones)

        # --- Sección: Progreso ---
        grupo_progreso = QGroupBox("Progreso")
        layout_progreso = QVBoxLayout(grupo_progreso)
        layout_progreso.setSpacing(6)

        self._barra_progreso = QProgressBar()
        self._barra_progreso.setRange(0, 100)
        self._barra_progreso.setValue(0)
        self._barra_progreso.setFormat("%p% — %v de %m líneas")
        self._barra_progreso.setTextVisible(True)

        self._lbl_estado = QLabel("Listo")
        self._lbl_estado.setStyleSheet(f"color: {COLOR_TEXTO_SECUNDARIO}; font-size: 11px;")

        layout_progreso.addWidget(self._barra_progreso)
        layout_progreso.addWidget(self._lbl_estado)

        layout_principal.addWidget(grupo_progreso)

        # --- Sección: Log en tiempo real ---
        grupo_log = QGroupBox("Registro de actividad")
        layout_log = QVBoxLayout(grupo_log)

        self._area_log = QTextEdit()
        self._area_log.setReadOnly(True)
        self._area_log.setProperty("class", "log")
        self._area_log.setMinimumHeight(180)
        self._area_log.setPlaceholderText(
            "El registro de carga aparecerá aquí durante el procesamiento..."
        )

        btn_limpiar_log = QPushButton("🗑  Limpiar log")
        btn_limpiar_log.setFixedWidth(130)
        btn_limpiar_log.clicked.connect(self._area_log.clear)

        fila_log_botones = QHBoxLayout()
        fila_log_botones.addStretch()
        fila_log_botones.addWidget(btn_limpiar_log)

        layout_log.addWidget(self._area_log)
        layout_log.addLayout(fila_log_botones)

        layout_principal.addWidget(grupo_log, stretch=1)

        # --- Sección: Resumen final ---
        self._grupo_resumen = QGroupBox("Resumen de última carga")
        layout_resumen = QHBoxLayout(self._grupo_resumen)

        self._lbl_cargados      = self._crear_chip_resumen("Cargados",     "0")
        self._lbl_descartados   = self._crear_chip_resumen("Descartados",  "0")
        self._lbl_con_adjuntos  = self._crear_chip_resumen("Con adjuntos", "0")
        self._lbl_media_omitida = self._crear_chip_resumen("Media omitida","0")

        layout_resumen.addWidget(self._lbl_cargados)
        layout_resumen.addWidget(self._lbl_descartados)
        layout_resumen.addWidget(self._lbl_con_adjuntos)
        layout_resumen.addWidget(self._lbl_media_omitida)
        layout_resumen.addStretch()

        self._grupo_resumen.setVisible(False)  # Oculto hasta primer parseo
        layout_principal.addWidget(self._grupo_resumen)

    def _crear_chip_resumen(self, etiqueta: str, valor: str) -> QWidget:
        """Crea un widget compuesto etiqueta + número para el resumen."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(2)

        lbl_valor = QLabel(valor)
        lbl_valor.setStyleSheet(
            f"color: {COLOR_ACENTO_CLARO}; font-size: 24px; font-weight: 700;"
        )
        lbl_valor.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_valor.setObjectName(f"chip_{etiqueta.lower().replace(' ', '_')}")

        lbl_etiq = QLabel(etiqueta)
        lbl_etiq.setStyleSheet(f"color: {COLOR_TEXTO_SECUNDARIO}; font-size: 10px;")
        lbl_etiq.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(lbl_valor)
        layout.addWidget(lbl_etiq)

        # Guardar referencia al label de valor para actualizarlo luego
        widget._lbl_valor = lbl_valor  # type: ignore[attr-defined]

        return widget

    # ------------------------------------------------------------------
    # Slots de interacción del usuario
    # ------------------------------------------------------------------

    def _seleccionar_archivo(self) -> None:
        """Abre el diálogo para seleccionar el archivo .txt de WhatsApp."""
        ruta_str, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar chat de WhatsApp",
            "",
            "Archivos de texto (*.txt);;Todos los archivos (*.*)",
        )
        if not ruta_str:
            return  # El usuario canceló

        ruta = Path(ruta_str)
        self._ruta_seleccionada = ruta
        self._lbl_ruta.setText(str(ruta))
        self._lbl_ruta.setStyleSheet("")  # Quitar itálica gris

        # Mostrar info del archivo
        try:
            size_kb = ruta.stat().st_size / 1024
            self._lbl_info_archivo.setText(
                f"Tamaño: {size_kb:.1f} KB  |  Última modificación: "
                f"{ruta.stat().st_mtime:.0f}"
            )
        except OSError:
            self._lbl_info_archivo.setText("No se pudo leer la información del archivo.")

        self._btn_cargar.setEnabled(True)
        self._agregar_log(f"📂 Archivo seleccionado: {ruta.name}")

    def _iniciar_parseo(self) -> None:
        """
        Inicia el parseo del archivo seleccionado.

        Si ya existen mensajes en BD, pregunta si desea agregar o reemplazar.
        """
        if not self._ruta_seleccionada:
            return

        # Verificar si ya hay mensajes en BD
        total_existente = repo_mensajes.contar()
        reemplazar = False

        if total_existente > 0:
            respuesta = QMessageBox.question(
                self,
                "Mensajes existentes",
                f"Ya hay {total_existente:,} mensajes en la base de datos.\n\n"
                "¿Qué desea hacer?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Cancel,
            )

            # Personalizar botones vía re-implementación simple
            # Yes = Reemplazar, No = Agregar, Cancel = Cancelar
            if respuesta == QMessageBox.StandardButton.Cancel:
                return
            elif respuesta == QMessageBox.StandardButton.Yes:
                # Pedir confirmación para reemplazar
                confirmar = QMessageBox.warning(
                    self,
                    "Confirmar reemplazo",
                    "Se eliminarán TODOS los mensajes existentes antes de cargar.\n\n"
                    "¿Está seguro?",
                    QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
                    QMessageBox.StandardButton.Cancel,
                )
                if confirmar != QMessageBox.StandardButton.Ok:
                    return
                reemplazar = True
            # Si No: reemplazar = False (agregar al final)

        # Bloquear controles durante el parseo
        self._set_controles_activos(False)
        self._barra_progreso.setValue(0)
        self._agregar_log(
            f"\n{'═' * 50}\n"
            f"▶ Iniciando parseo: {self._ruta_seleccionada.name}\n"
            f"  Modo: {'Reemplazar' if reemplazar else 'Agregar'}\n"
            f"{'═' * 50}"
        )
        self._lbl_estado.setText("Procesando...")

        # Crear y arrancar el hilo
        self._hilo = HiloParseo(self._ruta_seleccionada, reemplazar, self)
        self._hilo.progreso.connect(self._al_progreso)
        self._hilo.log.connect(self._agregar_log)
        self._hilo.terminado.connect(self._al_parseo_terminado)
        self._hilo.error.connect(self._al_parseo_error)
        self._hilo.start()

    def _cancelar_parseo(self) -> None:
        """
        Solicita cancelación del hilo de parseo.

        Nota: QThread.terminate() es peligroso; en su lugar se usa un flag
        en el parser que verifica periódicamente. Si el parser no implementa
        cancelación, el hilo se deja terminar naturalmente.
        """
        if self._hilo and self._hilo.isRunning():
            self._agregar_log("⚠ Cancelación solicitada — esperando fin de línea actual...")
            self._hilo.requestInterruption()  # El parser puede chequearlo (opcional)

    # ------------------------------------------------------------------
    # Slots del hilo de parseo
    # ------------------------------------------------------------------

    def _al_progreso(self, actual: int, total: int) -> None:
        """Actualiza la barra de progreso con el porcentaje calculado."""
        if total > 0:
            self._barra_progreso.setRange(0, total)
            self._barra_progreso.setValue(actual)

    def _al_parseo_terminado(self, resumen: ResumenParseo) -> None:
        """Muestra el resumen y notifica al visor que hay datos nuevos."""
        self._set_controles_activos(True)
        self._barra_progreso.setValue(self._barra_progreso.maximum())
        self._lbl_estado.setText("Completado")

        # Log final
        self._agregar_log("\n✅ Parseo completado")
        self._agregar_log(str(resumen))

        # Actualizar resumen visual
        self._actualizar_resumen(resumen)

        # Emitir señal para recargar la tabla en el visor
        self.parseo_completado.emit()

    def _al_parseo_error(self, mensaje_error: str) -> None:
        """Maneja errores durante el parseo y muestra un mensaje al usuario."""
        self._set_controles_activos(True)
        self._lbl_estado.setText("Error")
        self._agregar_log(f"❌ Error: {mensaje_error}")
        QMessageBox.critical(
            self,
            "Error al parsear",
            f"Ocurrió un error durante el parseo:\n\n{mensaje_error}",
        )

    # ------------------------------------------------------------------
    # Helpers internos
    # ------------------------------------------------------------------

    def _set_controles_activos(self, activos: bool) -> None:
        """Habilita/deshabilita controles durante el parseo."""
        self._btn_seleccionar.setEnabled(activos)
        self._btn_cargar.setEnabled(activos and self._ruta_seleccionada is not None)
        self._btn_cancelar.setEnabled(not activos)

    def _agregar_log(self, texto: str) -> None:
        """Agrega una línea al área de log."""
        self._area_log.append(texto)
        self._area_log.verticalScrollBar().setValue(
            self._area_log.verticalScrollBar().maximum()
        )

    def _actualizar_resumen(self, resumen: ResumenParseo) -> None:
        """Actualiza los chips de resumen con los datos del parseo."""
        self._grupo_resumen.setVisible(True)

        self._lbl_cargados._lbl_valor.setText(str(resumen.mensajes_cargados))  # type: ignore[attr-defined]
        self._lbl_descartados._lbl_valor.setText(str(resumen.mensajes_descartados))  # type: ignore[attr-defined]
        self._lbl_con_adjuntos._lbl_valor.setText(str(resumen.mensajes_con_adjuntos))  # type: ignore[attr-defined]
        self._lbl_media_omitida._lbl_valor.setText(str(resumen.mensajes_con_media_omitida))  # type: ignore[attr-defined]

        # Colorizar los chips según el tipo
        self._lbl_cargados._lbl_valor.setStyleSheet(
            f"color: {COLOR_PROCESADO_TXT}; font-size: 24px; font-weight: 700;"
        )
        self._lbl_descartados._lbl_valor.setStyleSheet(
            f"color: {COLOR_ERROR_TXT}; font-size: 24px; font-weight: 700;"
        )
        self._lbl_con_adjuntos._lbl_valor.setStyleSheet(
            f"color: {COLOR_ACENTO_CLARO}; font-size: 24px; font-weight: 700;"
        )
        self._lbl_media_omitida._lbl_valor.setStyleSheet(
            f"color: {COLOR_SIN_PROCESAR_TXT}; font-size: 24px; font-weight: 700;"
        )
