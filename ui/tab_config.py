"""
ui/tab_config.py
----------------
Tab de configuración: rutas y apariencia (Etapa 3).
"""

from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import (
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QCheckBox,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from config import (
    CONFIG_DIR_MULTIMEDIA,
    CONFIG_TAMANO_FUENTE,
    CONFIG_TEMA,
    CONFIG_PROVEEDOR_IA,
    CONFIG_KEY_OPENAI,
    CONFIG_TAMANO_LOTE,
    CONFIG_PAUSA_LOTES,
    CONFIG_AGREGAR_EQUIPOS_AUTO,
    CONFIG_CONFIRMAR_TODOS,
)
from database.connection import db
from config import DB_PATH


def _get_config(clave: str, default: str = "") -> str:
    conn = db.get_connection()
    cur = conn.cursor()
    cur.execute("SELECT valor FROM configuracion WHERE clave = ?", (clave,))
    row = cur.fetchone()
    return row[0] if row and row[0] is not None else default


def _set_config(clave: str, valor: str) -> None:
    conn = db.get_connection()
    conn.execute(
        "INSERT OR REPLACE INTO configuracion (clave, valor) VALUES (?, ?)",
        (clave, valor),
    )
    conn.commit()


class TabConfig(QWidget):
    """Tab de configuración de la aplicación."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._construir_ui()
        self._cargar_valores()

    def _construir_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # --- Sección Archivos y Rutas ---
        grupo_rutas = QGroupBox("Archivos y rutas")
        layout_rutas = QVBoxLayout(grupo_rutas)

        fila_dir = QHBoxLayout()
        self._campo_multimedia = QLineEdit()
        btn_explorar = QPushButton("Explorar")
        btn_explorar.clicked.connect(self._explorar_multimedia)
        fila_dir.addWidget(QLabel("Directorio multimedia:"))
        fila_dir.addWidget(self._campo_multimedia, stretch=1)
        fila_dir.addWidget(btn_explorar)
        layout_rutas.addLayout(fila_dir)

        fila_bd = QHBoxLayout()
        self._campo_bd = QLineEdit(str(DB_PATH))
        self._campo_bd.setReadOnly(True)
        btn_abrir_bd = QPushButton("Abrir carpeta de datos")
        btn_abrir_bd.clicked.connect(self._abrir_carpeta_bd)
        fila_bd.addWidget(QLabel("Base de datos:"))
        fila_bd.addWidget(self._campo_bd, stretch=1)
        fila_bd.addWidget(btn_abrir_bd)
        layout_rutas.addLayout(fila_bd)

        layout.addWidget(grupo_rutas)

        # --- Sección IA (OpenAI) ---
        grupo_ia = QGroupBox("Proveedor IA")
        layout_ia = QVBoxLayout(grupo_ia)

        fila_prov = QHBoxLayout()
        self._combo_proveedor = QLineEdit()
        self._combo_proveedor.setReadOnly(True)
        self._combo_proveedor.setText("openai")
        fila_prov.addWidget(QLabel("Proveedor:"))
        fila_prov.addWidget(self._combo_proveedor)
        layout_ia.addLayout(fila_prov)

        fila_key = QHBoxLayout()
        self._campo_api_key = QLineEdit()
        self._campo_api_key.setEchoMode(QLineEdit.EchoMode.Password)
        btn_toggle = QPushButton("Mostrar")
        btn_toggle.clicked.connect(self._toggle_key)
        fila_key.addWidget(QLabel("API Key:") )
        fila_key.addWidget(self._campo_api_key, stretch=1)
        fila_key.addWidget(btn_toggle)
        layout_ia.addLayout(fila_key)

        fila_modelo = QHBoxLayout()
        self._campo_modelo = QLineEdit()
        fila_modelo.addWidget(QLabel("Modelo:"))
        fila_modelo.addWidget(self._campo_modelo, stretch=1)
        layout_ia.addLayout(fila_modelo)

        btn_probar = QPushButton("Probar conexion")
        btn_probar.clicked.connect(self._probar_conexion)
        layout_ia.addWidget(btn_probar)

        layout.addWidget(grupo_ia)

        # --- Sección Procesamiento ---
        grupo_proc = QGroupBox("Procesamiento")
        layout_proc = QHBoxLayout(grupo_proc)
        self._spin_lote = QSpinBox()
        self._spin_lote.setRange(10, 200)
        self._spin_pausa = QSpinBox()
        self._spin_pausa.setRange(0, 10)
        self._check_auto = QCheckBox("Agregar equipos sugeridos")
        self._check_confirm = QCheckBox("Confirmar procesar todos")

        layout_proc.addWidget(QLabel("Tamaño lote:"))
        layout_proc.addWidget(self._spin_lote)
        layout_proc.addSpacing(12)
        layout_proc.addWidget(QLabel("Pausa (s):"))
        layout_proc.addWidget(self._spin_pausa)
        layout_proc.addSpacing(12)
        layout_proc.addWidget(self._check_auto)
        layout_proc.addWidget(self._check_confirm)
        layout_proc.addStretch()

        layout.addWidget(grupo_proc)

        # --- Sección Apariencia ---
        grupo_apariencia = QGroupBox("Apariencia")
        layout_ap = QHBoxLayout(grupo_apariencia)

        self._combo_tema = QLineEdit()
        self._combo_tema.setPlaceholderText("claro / oscuro")
        self._spin_fuente = QSpinBox()
        self._spin_fuente.setRange(9, 16)

        layout_ap.addWidget(QLabel("Tema:"))
        layout_ap.addWidget(self._combo_tema)
        layout_ap.addSpacing(12)
        layout_ap.addWidget(QLabel("Tamaño fuente tabla:"))
        layout_ap.addWidget(self._spin_fuente)
        layout_ap.addStretch()

        layout.addWidget(grupo_apariencia)

        # Botones
        fila_botones = QHBoxLayout()
        btn_guardar = QPushButton("Guardar cambios")
        btn_guardar.setProperty("class", "primario")
        btn_guardar.clicked.connect(self._guardar)
        fila_botones.addStretch()
        fila_botones.addWidget(btn_guardar)
        layout.addLayout(fila_botones)

        layout.addStretch()

    def _cargar_valores(self) -> None:
        self._campo_multimedia.setText(_get_config(CONFIG_DIR_MULTIMEDIA, ""))
        self._combo_tema.setText(_get_config(CONFIG_TEMA, "claro"))
        self._spin_fuente.setValue(int(_get_config(CONFIG_TAMANO_FUENTE, "11")))
        self._campo_api_key.setText(_get_config(CONFIG_KEY_OPENAI, ""))
        self._campo_modelo.setText(_get_config("modelo_openai", "gpt-4o-mini"))
        self._spin_lote.setValue(int(_get_config(CONFIG_TAMANO_LOTE, "50")))
        self._spin_pausa.setValue(int(_get_config(CONFIG_PAUSA_LOTES, "1")))
        self._check_auto.setChecked(_get_config(CONFIG_AGREGAR_EQUIPOS_AUTO, "1") == "1")
        self._check_confirm.setChecked(_get_config(CONFIG_CONFIRMAR_TODOS, "1") == "1")

    def _guardar(self) -> None:
        _set_config(CONFIG_DIR_MULTIMEDIA, self._campo_multimedia.text().strip())
        _set_config(CONFIG_TEMA, self._combo_tema.text().strip() or "claro")
        _set_config(CONFIG_TAMANO_FUENTE, str(self._spin_fuente.value()))
        _set_config(CONFIG_PROVEEDOR_IA, "openai")
        _set_config(CONFIG_KEY_OPENAI, self._campo_api_key.text().strip())
        _set_config("modelo_openai", self._campo_modelo.text().strip() or "gpt-4o-mini")
        _set_config(CONFIG_TAMANO_LOTE, str(self._spin_lote.value()))
        _set_config(CONFIG_PAUSA_LOTES, str(self._spin_pausa.value()))
        _set_config(CONFIG_AGREGAR_EQUIPOS_AUTO, "1" if self._check_auto.isChecked() else "0")
        _set_config(CONFIG_CONFIRMAR_TODOS, "1" if self._check_confirm.isChecked() else "0")

    def _explorar_multimedia(self) -> None:
        ruta = QFileDialog.getExistingDirectory(
            self,
            "Seleccionar directorio multimedia",
            self._campo_multimedia.text().strip() or str(Path.home()),
        )
        if ruta:
            self._campo_multimedia.setText(ruta)

    def _abrir_carpeta_bd(self) -> None:
        import os
        os.startfile(str(DB_PATH.parent))

    def _toggle_key(self) -> None:
        modo = self._campo_api_key.echoMode()
        if modo == QLineEdit.EchoMode.Password:
            self._campo_api_key.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self._campo_api_key.setEchoMode(QLineEdit.EchoMode.Password)

    def _probar_conexion(self) -> None:
        from ai.openai_client import OpenAIClient
        api_key = self._campo_api_key.text().strip()
        if not api_key:
            QMessageBox.warning(self, "API Key", "La API key esta vacia.")
            return
        client = OpenAIClient(api_key, self._campo_modelo.text().strip() or "gpt-4o-mini")
        try:
            client.classify_batch(
                messages=[{"id": 1, "texto": "Prueba"}],
                equipment_list=[],
                prompt_base="Responde con un JSON: [{\"id\":1,\"equipo\":null,\"tipo_mensaje\":\"otro\"}]",
            )
            QMessageBox.information(self, "Conexion", "OK")
        except Exception as exc:
            QMessageBox.warning(self, "Conexion", str(exc))
