"""
database/connection.py
----------------------
Singleton de conexión a SQLite para PalmaMtto Desktop.

Decisión de diseño: se usa el patrón Singleton con threading.Lock para
garantizar una sola conexión compartida entre todos los módulos de la app.
check_same_thread=False es seguro aquí porque PyQt6 serializa las
operaciones de BD a través del hilo principal; los QThread de parseo usan
la misma conexión pero con commits explícitos y sin transacciones anidadas.

Se activa WAL (Write-Ahead Logging) para mejor rendimiento y se habilitan
las claves foráneas, que SQLite desactiva por defecto.
"""

import sqlite3
import threading
from pathlib import Path
from typing import Optional

from config import DB_PATH


class DatabaseConnection:
    """
    Gestiona la conexión singleton a la base de datos SQLite.

    Uso típico:
        from database.connection import db
        db.connect()                    # Una vez al arrancar la app
        conn = db.get_connection()      # En cualquier repositorio
    """

    _instance: Optional["DatabaseConnection"] = None
    _lock: threading.Lock = threading.Lock()

    def __new__(cls) -> "DatabaseConnection":
        """Garantiza que solo exista una instancia (patrón Singleton)."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._connection: Optional[sqlite3.Connection] = None
        return cls._instance

    # ------------------------------------------------------------------
    # Ciclo de vida
    # ------------------------------------------------------------------

    def connect(self, db_path: Path = DB_PATH) -> None:
        """
        Abre la conexión a la base de datos.

        Puede llamarse varias veces de forma segura; solo abre la conexión
        la primera vez. Esto permite que distintos módulos llamen connect()
        en su inicialización sin efectos secundarios.

        Args:
            db_path: Ruta al archivo .db. Por defecto usa DB_PATH de config.
        """
        if self._connection is None:
            self._connection = sqlite3.connect(
                str(db_path),
                check_same_thread=False,  # Ver nota en docstring del módulo
            )
            # Usar Row para acceso por nombre de columna (row["campo"])
            self._connection.row_factory = sqlite3.Row

            # Habilitar integridad referencial (desactivada por defecto en SQLite)
            self._connection.execute("PRAGMA foreign_keys = ON")

            # WAL: mejor rendimiento en lecturas concurrentes con escrituras
            self._connection.execute("PRAGMA journal_mode = WAL")

            # Sincronización normal: balance entre seguridad y velocidad
            self._connection.execute("PRAGMA synchronous = NORMAL")

            self._connection.commit()

    def get_connection(self) -> sqlite3.Connection:
        """
        Retorna la conexión activa.

        Raises:
            RuntimeError: Si connect() no ha sido llamado todavía.
        """
        if self._connection is None:
            raise RuntimeError(
                "Base de datos no inicializada. "
                "Llama db.connect() antes de usar los repositorios."
            )
        return self._connection

    def close(self) -> None:
        """
        Cierra la conexión y libera recursos.
        Se debe llamar al salir de la aplicación (closeEvent de la ventana).
        """
        if self._connection is not None:
            self._connection.close()
            self._connection = None

    # ------------------------------------------------------------------
    # Utilidades
    # ------------------------------------------------------------------

    def is_connected(self) -> bool:
        """Retorna True si hay una conexión activa."""
        return self._connection is not None

    def ejecutar_script(self, sql: str) -> None:
        """
        Ejecuta un bloque SQL de múltiples sentencias (útil para migraciones).

        Args:
            sql: Cadena con una o varias sentencias SQL separadas por ';'.
        """
        conn = self.get_connection()
        conn.executescript(sql)
        conn.commit()


# ---------------------------------------------------------------------------
# Instancia global — se importa desde todos los módulos de BD
# ---------------------------------------------------------------------------
db = DatabaseConnection()

# ---------------------------------------------------------------------------
# Siguiente archivo a construir: database/schema.py
# ---------------------------------------------------------------------------
