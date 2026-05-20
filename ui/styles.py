"""
ui/styles.py
------------
Paleta de colores y estilos QSS (Qt Style Sheets) globales para PalmaMtto Desktop.

Decisión de diseño: se define una paleta industrial/utilitaria coherente con el
contexto de una planta extractora de aceite de palma. Colores oscuros con
acento en verde palma (verde oliva) para jerarquía visual, sin distracciones.
Los estilos QSS se centralizan aquí para que cualquier widget pueda importarlos
sin duplicar código.

Los chips de estado (sin_procesar, procesado, error) usan colores semáforo que
el módulo message_table.py aplica como celdas de color.
"""

# ---------------------------------------------------------------------------
# Paleta de colores (para uso en Python, no solo en QSS)
# ---------------------------------------------------------------------------

# Fondos
COLOR_BG_PRINCIPAL    = "#1E2022"   # Fondo de la ventana principal
COLOR_BG_SECUNDARIO   = "#252A2D"   # Fondo de panels / sidebars
COLOR_BG_WIDGET       = "#2D3337"   # Fondo de campos de texto, combobox
COLOR_BG_HOVER        = "#353B40"   # Hover sobre filas de tabla
COLOR_BG_SELECCION    = "#2C4A2E"   # Fila seleccionada (verde oscuro)

# Texto
COLOR_TEXTO_PRINCIPAL = "#E8E6E1"   # Texto principal (casi blanco cálido)
COLOR_TEXTO_SECUNDARIO = "#9EA8A0"  # Texto secundario / placeholders
COLOR_TEXTO_DESACTIVADO = "#5C6560" # Texto desactivado

# Acento
COLOR_ACENTO          = "#5A8A3C"   # Verde palma — acento principal
COLOR_ACENTO_CLARO    = "#6FA84A"   # Verde más brillante para hover
COLOR_ACENTO_OSCURO   = "#3D6128"   # Verde oscuro para pressed

# Bordes
COLOR_BORDE           = "#3A4040"   # Bordes generales
COLOR_BORDE_ACTIVO    = "#5A8A3C"   # Borde de campo enfocado

# Estados de proceso (chips de color)
COLOR_SIN_PROCESAR    = "#5A5A3A"   # Amarillo oscuro / mostaza
COLOR_SIN_PROCESAR_TXT = "#D4CC6A"
COLOR_PROCESADO       = "#2E5C2E"   # Verde oscuro
COLOR_PROCESADO_TXT   = "#7ECF7E"
COLOR_ERROR           = "#5C2E2E"   # Rojo oscuro
COLOR_ERROR_TXT       = "#E07070"

# Tipos de mensaje (para colores opcionales en la tabla)
TIPO_COLORES = {
    "intervencion": "#3A4A5C",   # Azul acero
    "informativo":  "#3A4A40",   # Verde grisáceo
    "solicitud":    "#5C4A2E",   # Naranja oscuro
    "relleno":      "#3A3A3A",   # Gris neutro
    "otro":         "#2E2E3A",   # Morado oscuro
}

# ---------------------------------------------------------------------------
# Hoja de estilos QSS principal
# ---------------------------------------------------------------------------

QSS_PRINCIPAL = f"""
/* ====== Ventana y fondos base ====== */
QMainWindow, QDialog {{
    background-color: {COLOR_BG_PRINCIPAL};
    color: {COLOR_TEXTO_PRINCIPAL};
    font-family: "Segoe UI", "Noto Sans", sans-serif;
    font-size: 13px;
}}

QWidget {{
    background-color: transparent;
    color: {COLOR_TEXTO_PRINCIPAL};
    font-family: "Segoe UI", "Noto Sans", sans-serif;
    font-size: 13px;
}}

/* ====== Tab principal ====== */
QTabWidget::pane {{
    background-color: {COLOR_BG_SECUNDARIO};
    border: 1px solid {COLOR_BORDE};
    border-top: none;
}}

QTabBar::tab {{
    background-color: {COLOR_BG_WIDGET};
    color: {COLOR_TEXTO_SECUNDARIO};
    padding: 8px 20px;
    border: 1px solid {COLOR_BORDE};
    border-bottom: none;
    margin-right: 2px;
    font-weight: 500;
    min-width: 110px;
}}

QTabBar::tab:selected {{
    background-color: {COLOR_BG_SECUNDARIO};
    color: {COLOR_TEXTO_PRINCIPAL};
    border-top: 2px solid {COLOR_ACENTO};
}}

QTabBar::tab:hover:!selected {{
    background-color: {COLOR_BG_HOVER};
    color: {COLOR_TEXTO_PRINCIPAL};
}}

/* ====== Botones ====== */
QPushButton {{
    background-color: {COLOR_BG_WIDGET};
    color: {COLOR_TEXTO_PRINCIPAL};
    border: 1px solid {COLOR_BORDE};
    border-radius: 4px;
    padding: 6px 14px;
    font-weight: 500;
}}

QPushButton:hover {{
    background-color: {COLOR_BG_HOVER};
    border-color: {COLOR_ACENTO};
}}

QPushButton:pressed {{
    background-color: {COLOR_ACENTO_OSCURO};
}}

QPushButton:disabled {{
    color: {COLOR_TEXTO_DESACTIVADO};
    border-color: {COLOR_BORDE};
}}

/* Botón primario (acción principal) */
QPushButton[class="primario"] {{
    background-color: {COLOR_ACENTO};
    color: #FFFFFF;
    border: none;
    font-weight: 600;
}}

QPushButton[class="primario"]:hover {{
    background-color: {COLOR_ACENTO_CLARO};
}}

QPushButton[class="primario"]:pressed {{
    background-color: {COLOR_ACENTO_OSCURO};
}}

/* ====== Campos de texto ====== */
QLineEdit, QTextEdit, QPlainTextEdit {{
    background-color: {COLOR_BG_WIDGET};
    color: {COLOR_TEXTO_PRINCIPAL};
    border: 1px solid {COLOR_BORDE};
    border-radius: 4px;
    padding: 5px 8px;
    selection-background-color: {COLOR_ACENTO};
}}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
    border-color: {COLOR_BORDE_ACTIVO};
}}

QLineEdit:disabled {{
    color: {COLOR_TEXTO_DESACTIVADO};
    background-color: {COLOR_BG_SECUNDARIO};
}}

/* ====== ComboBox ====== */
QComboBox {{
    background-color: {COLOR_BG_WIDGET};
    color: {COLOR_TEXTO_PRINCIPAL};
    border: 1px solid {COLOR_BORDE};
    border-radius: 4px;
    padding: 5px 8px;
    min-width: 120px;
}}

QComboBox:hover {{
    border-color: {COLOR_ACENTO};
}}

QComboBox::drop-down {{
    border: none;
    width: 20px;
}}

QComboBox::down-arrow {{
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 6px solid {COLOR_TEXTO_SECUNDARIO};
    margin-right: 6px;
}}

QComboBox QAbstractItemView {{
    background-color: {COLOR_BG_WIDGET};
    color: {COLOR_TEXTO_PRINCIPAL};
    border: 1px solid {COLOR_BORDE};
    selection-background-color: {COLOR_ACENTO};
    outline: none;
}}

/* ====== SpinBox ====== */
QSpinBox {{
    background-color: {COLOR_BG_WIDGET};
    color: {COLOR_TEXTO_PRINCIPAL};
    border: 1px solid {COLOR_BORDE};
    border-radius: 4px;
    padding: 4px 6px;
}}

QSpinBox:focus {{
    border-color: {COLOR_BORDE_ACTIVO};
}}

/* ====== CheckBox ====== */
QCheckBox {{
    color: {COLOR_TEXTO_PRINCIPAL};
    spacing: 6px;
}}

QCheckBox::indicator {{
    width: 15px;
    height: 15px;
    border: 1px solid {COLOR_BORDE};
    border-radius: 3px;
    background-color: {COLOR_BG_WIDGET};
}}

QCheckBox::indicator:checked {{
    background-color: {COLOR_ACENTO};
    border-color: {COLOR_ACENTO};
}}

/* ====== Labels ====== */
QLabel {{
    color: {COLOR_TEXTO_PRINCIPAL};
    background: transparent;
}}

QLabel[class="seccion"] {{
    color: {COLOR_ACENTO_CLARO};
    font-weight: 700;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 1px;
}}

QLabel[class="contador"] {{
    color: {COLOR_TEXTO_SECUNDARIO};
    font-size: 12px;
}}

/* ====== Barra de progreso ====== */
QProgressBar {{
    background-color: {COLOR_BG_WIDGET};
    border: 1px solid {COLOR_BORDE};
    border-radius: 4px;
    text-align: center;
    color: {COLOR_TEXTO_PRINCIPAL};
    font-size: 11px;
    height: 18px;
}}

QProgressBar::chunk {{
    background-color: {COLOR_ACENTO};
    border-radius: 3px;
}}

/* ====== ScrollBar ====== */
QScrollBar:vertical {{
    background-color: {COLOR_BG_SECUNDARIO};
    width: 8px;
    border: none;
}}

QScrollBar::handle:vertical {{
    background-color: {COLOR_BORDE};
    border-radius: 4px;
    min-height: 30px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {COLOR_TEXTO_DESACTIVADO};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QScrollBar:horizontal {{
    background-color: {COLOR_BG_SECUNDARIO};
    height: 8px;
    border: none;
}}

QScrollBar::handle:horizontal {{
    background-color: {COLOR_BORDE};
    border-radius: 4px;
    min-width: 30px;
}}

QScrollBar::handle:horizontal:hover {{
    background-color: {COLOR_TEXTO_DESACTIVADO};
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0px;
}}

/* ====== Tabla (QTableView / QTableWidget) ====== */
QTableView, QTableWidget {{
    background-color: {COLOR_BG_SECUNDARIO};
    alternate-background-color: {COLOR_BG_WIDGET};
    color: {COLOR_TEXTO_PRINCIPAL};
    gridline-color: {COLOR_BORDE};
    border: 1px solid {COLOR_BORDE};
    selection-background-color: {COLOR_BG_SELECCION};
    selection-color: {COLOR_TEXTO_PRINCIPAL};
    font-size: 12px;
}}

QTableView::item:hover {{
    background-color: {COLOR_BG_HOVER};
}}

QHeaderView::section {{
    background-color: {COLOR_BG_PRINCIPAL};
    color: {COLOR_TEXTO_SECUNDARIO};
    border: none;
    border-right: 1px solid {COLOR_BORDE};
    border-bottom: 1px solid {COLOR_BORDE};
    padding: 5px 8px;
    font-weight: 600;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}}

QHeaderView::section:hover {{
    background-color: {COLOR_BG_WIDGET};
    color: {COLOR_TEXTO_PRINCIPAL};
}}

/* ====== Área de log (QTextEdit) ====== */
QTextEdit[class="log"] {{
    background-color: {COLOR_BG_PRINCIPAL};
    color: {COLOR_TEXTO_SECUNDARIO};
    border: 1px solid {COLOR_BORDE};
    border-radius: 4px;
    font-family: "Consolas", "Courier New", monospace;
    font-size: 12px;
    padding: 4px;
}}

/* ====== GroupBox ====== */
QGroupBox {{
    border: 1px solid {COLOR_BORDE};
    border-radius: 6px;
    margin-top: 12px;
    padding-top: 10px;
    color: {COLOR_TEXTO_SECUNDARIO};
    font-size: 11px;
    font-weight: 600;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 4px;
    color: {COLOR_ACENTO_CLARO};
}}

/* ====== Splitter ====== */
QSplitter::handle {{
    background-color: {COLOR_BORDE};
    width: 1px;
    height: 1px;
}}

/* ====== ToolTip ====== */
QToolTip {{
    background-color: {COLOR_BG_WIDGET};
    color: {COLOR_TEXTO_PRINCIPAL};
    border: 1px solid {COLOR_ACENTO};
    padding: 4px 8px;
    font-size: 12px;
}}

/* ====== Barra de menú ====== */
QMenuBar {{
    background-color: {COLOR_BG_PRINCIPAL};
    color: {COLOR_TEXTO_PRINCIPAL};
    border-bottom: 1px solid {COLOR_BORDE};
}}

QMenuBar::item:selected {{
    background-color: {COLOR_BG_HOVER};
}}

QMenu {{
    background-color: {COLOR_BG_WIDGET};
    color: {COLOR_TEXTO_PRINCIPAL};
    border: 1px solid {COLOR_BORDE};
}}

QMenu::item:selected {{
    background-color: {COLOR_ACENTO};
    color: #FFFFFF;
}}

QMenu::separator {{
    height: 1px;
    background-color: {COLOR_BORDE};
    margin: 3px 0;
}}

/* ====== StatusBar ====== */
QStatusBar {{
    background-color: {COLOR_BG_PRINCIPAL};
    color: {COLOR_TEXTO_SECUNDARIO};
    border-top: 1px solid {COLOR_BORDE};
    font-size: 11px;
}}
"""


def aplicar_estilos(app) -> None:
    """
    Aplica la hoja de estilos global a la aplicación PyQt6.

    Llamar una sola vez desde main.py después de crear QApplication.

    Args:
        app: Instancia de QApplication.
    """
    app.setStyleSheet(QSS_PRINCIPAL)


def color_estado_proceso(estado: str) -> tuple[str, str]:
    """
    Retorna (color_fondo, color_texto) para un estado de proceso dado.

    Usado por message_table.py para colorear celdas de estado.

    Args:
        estado: "sin_procesar" | "procesado" | "error"

    Returns:
        Tupla (fondo_hex, texto_hex).
    """
    mapa = {
        "sin_procesar": (COLOR_SIN_PROCESAR, COLOR_SIN_PROCESAR_TXT),
        "procesado":    (COLOR_PROCESADO,    COLOR_PROCESADO_TXT),
        "error":        (COLOR_ERROR,         COLOR_ERROR_TXT),
    }
    return mapa.get(estado, (COLOR_BG_WIDGET, COLOR_TEXTO_PRINCIPAL))


# ---------------------------------------------------------------------------
# Siguiente archivo a construir: ui/widgets/message_table.py
# ---------------------------------------------------------------------------
