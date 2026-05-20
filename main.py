"""
main.py
-------
Punto de entrada de PalmaMtto Desktop — Etapa 2.

Arranca la aplicación PyQt6 con la ventana principal.
Mantiene el modo de consola (--parsear) de la Etapa 1 para pruebas rápidas
sin abrir la GUI.

Uso:
    python main.py                              # Abre la aplicación gráfica
    python main.py --parsear ruta/chat.txt      # Modo consola (sin GUI)
    python main.py --parsear ruta.txt --reemplazar
"""

import argparse
import sys
from pathlib import Path

from config import APP_NAME, APP_VERSION, DB_PATH
from database.connection import db
from database.schema import inicializar


def inicializar_base_de_datos() -> None:
    """Conecta a SQLite y crea las tablas si no existen."""
    db.connect(DB_PATH)
    inicializar()


def modo_consola_parsear(ruta_txt: str, reemplazar: bool) -> None:
    """
    Modo de prueba sin UI: parsea un archivo .txt y muestra el resumen.
    (Heredado de Etapa 1 para testing rápido.)
    """
    from parser.whatsapp_parser import parsear_archivo

    ruta = Path(ruta_txt)
    print(f"\nParsando: {ruta}")
    print("-" * 50)

    def progreso(actual: int, total: int) -> None:
        pct = int(actual / total * 100) if total > 0 else 0
        print(f"  Progreso: {pct}% ({actual}/{total} líneas)", end="\r")

    resumen = parsear_archivo(ruta, reemplazar=reemplazar, callback_progreso=progreso)
    print()
    print(resumen)

    if resumen.advertencias:
        print("\nAdvertencias:")
        for adv in resumen.advertencias[:10]:
            print(f"  ⚠  {adv}")
        if len(resumen.advertencias) > 10:
            print(f"  ... y {len(resumen.advertencias) - 10} más.")

    import database.repo_mensajes as repo_mensajes
    total_bd = repo_mensajes.contar()
    print(f"\nTotal en base de datos: {total_bd} mensajes")

    db.close()


def modo_gui() -> None:
    """Arranca la interfaz gráfica PyQt6."""
    # Importar PyQt6 solo en modo GUI para no romper el modo consola
    # si PyQt6 no está instalado en el entorno de prueba
    try:
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import Qt
    except ImportError:
        print(
            "ERROR: PyQt6 no está instalado.\n"
            "Ejecuta: pip install PyQt6\n"
            "O usa el modo consola: python main.py --parsear archivo.txt"
        )
        sys.exit(1)

    # Crear la aplicación Qt
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)

    # Aplicar hoja de estilos global
    from ui.styles import aplicar_estilos
    aplicar_estilos(app)

    # Crear y mostrar la ventana principal
    from ui.main_window import MainWindow
    ventana = MainWindow()
    ventana.show()

    # Bucle de eventos
    sys.exit(app.exec())


def main() -> None:
    """Función principal con despacho CLI → consola o GUI."""
    print(f"{APP_NAME} v{APP_VERSION}")
    print("=" * 50)

    # Parseo de argumentos
    parser_args = argparse.ArgumentParser(
        description=f"{APP_NAME} — Herramienta de gestión de mantenimiento"
    )
    parser_args.add_argument(
        "--parsear",
        metavar="ARCHIVO.TXT",
        help="Ruta al archivo .txt exportado de WhatsApp (modo consola, sin GUI)",
    )
    parser_args.add_argument(
        "--reemplazar",
        action="store_true",
        help="Eliminar mensajes existentes antes de cargar (solo con --parsear)",
    )
    args = parser_args.parse_args()

    # Inicializar BD siempre (crea las tablas si no existen)
    inicializar_base_de_datos()

    if args.parsear:
        # Modo consola heredado de Etapa 1
        modo_consola_parsear(args.parsear, args.reemplazar)
    else:
        # Modo gráfico: PyQt6
        modo_gui()


if __name__ == "__main__":
    main()


# ---------------------------------------------------------------------------
# Etapa 2 completada. Próxima etapa:
#   Etapa 3 — Filtros completos, EditDialog, MediaViewer, exportación
#   Archivos a construir:
#     ui/widgets/filter_panel.py
#     ui/widgets/edit_dialog.py
#     ui/widgets/media_viewer.py
#     ui/widgets/equip_manager.py
#     ui/tab_config.py
#     database/repo_equipos.py
#     export/csv_exporter.py
#     export/excel_exporter.py
#     export/json_exporter.py
# ---------------------------------------------------------------------------
