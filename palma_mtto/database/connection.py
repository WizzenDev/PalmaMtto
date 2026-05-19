import sqlite3
import threading

_DB_PATH = 'palma_mtto.db'  # Cambiar en config.py si quieres otro path
_conn = None
_lock = threading.Lock()

def get_connection():
    global _conn
    if _conn is None:
        with _lock:
            if _conn is None:
                _conn = sqlite3.connect(_DB_PATH)
                _conn.row_factory = sqlite3.Row
    return _conn
