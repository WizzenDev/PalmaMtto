"""
test_etapa1.py
--------------
Script de prueba para la Etapa 1 de PalmaMtto Desktop.

Ejecutar desde la raíz del proyecto (carpeta palma_mtto/):
    cd palma_mtto
    python test_etapa1.py

Prueba todos los componentes de la Etapa 1 sin necesidad de PyQt6
ni de un archivo .txt real. Usa mensajes de muestra codificados en el
propio script.
"""

import sys
import tempfile
from pathlib import Path

# ---------------------------------------------------------------------------
# Asegurar que el directorio raíz del proyecto esté en sys.path
# ---------------------------------------------------------------------------
# Esto permite importar los módulos (config, database, parser) sin instalar
# el paquete, útil para pruebas rápidas desde la carpeta del proyecto.
_RAIZ = Path(__file__).parent.resolve()
if str(_RAIZ) not in sys.path:
    sys.path.insert(0, str(_RAIZ))


# ---------------------------------------------------------------------------
# Datos de muestra: fragmento de chat de WhatsApp
# ---------------------------------------------------------------------------

CHAT_MUESTRA = """\
1/16/26, 7:00 AM - Sistema: Messages and calls are end-to-end encrypted. No one outside of this chat, not even WhatsApp, can read or listen to them.
1/16/26, 7:05 AM - Jimmy Electrico: Buenos dias
1/16/26, 7:15 AM - Pedro Mecanico: Se montan 120GL de Acpm en prensa #7
continua falla en rodamiento principal
1/16/26, 8:30 AM - Luis Supervisor: IMG-20260116-WA0028.jpg (file attached) foto del rodamiento fallado
1/16/26, 9:00 AM - Maria Almacen: (media omitted)
1/16/26, 9:15 AM - Carlos Electrico: Se revisa tablero de control digestor #1
se encontro fusible quemado, se reemplaza
1/16/26, 10:00 AM - Pedro Mecanico: Solicito correa tipo B para transportador de fibra
1/16/26, 11:30 AM - Jimmy Electrico: IMG-20260116-WA0041.jpg (file attached) IMG-20260116-WA0042.jpg (file attached) evidencia del trabajo
1/16/26, 4:33 PM - Jimmy - CeresAgro Electrico: Se montan 120GL de Acpm
1/17/26, 8:00 AM - Pedro Mecanico: Prensa #3 presenta vibración excesiva
requiere revisión de chumaceras
1/17/26, 9:30 AM - @Luis Supervisor
1/17/26, 10:00 AM - Sistema: created group "Mantenimiento Planta"
""".strip()


# ---------------------------------------------------------------------------
# Colores para terminal (opcional, solo estético)
# ---------------------------------------------------------------------------

class C:
    OK    = "\033[92m"  # Verde
    WARN  = "\033[93m"  # Amarillo
    ERR   = "\033[91m"  # Rojo
    BOLD  = "\033[1m"
    RESET = "\033[0m"


def ok(msg: str) -> None:
    print(f"  {C.OK}✓{C.RESET} {msg}")


def warn(msg: str) -> None:
    print(f"  {C.WARN}⚠{C.RESET} {msg}")


def err(msg: str) -> None:
    print(f"  {C.ERR}✗{C.RESET} {msg}")


def titulo(msg: str) -> None:
    print(f"\n{C.BOLD}{msg}{C.RESET}")
    print("─" * 60)


# ---------------------------------------------------------------------------
# Tests individuales
# ---------------------------------------------------------------------------

def test_config() -> bool:
    """Verifica que config.py se importa correctamente."""
    titulo("TEST 1: config.py")
    try:
        import config
        ok(f"APP_NAME = '{config.APP_NAME}'")
        ok(f"DB_PATH  = {config.DB_PATH}")
        ok(f"TIPOS_MENSAJE = {config.TIPOS_MENSAJE}")
        ok(f"EXTENSIONES_ADJUNTOS = {config.EXTENSIONES_ADJUNTOS}")
        return True
    except Exception as e:
        err(f"Error en config.py: {e}")
        return False


def test_database(db_path: Path) -> bool:
    """Verifica conexión, creación de tablas y configuración predeterminada."""
    titulo("TEST 2: database (connection + schema + models)")
    try:
        from database.connection import db
        from database.schema import inicializar
        from database.models import Mensaje, Lote, Equipo, Configuracion

        # Conectar con BD temporal
        db.connect(db_path)
        ok(f"Conexión abierta en {db_path.name}")

        # Crear tablas
        inicializar()
        ok("Tablas creadas (o ya existían)")

        # Verificar que las tablas existen
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tablas = {row[0] for row in cursor.fetchall()}
        for tabla_esperada in ("mensajes", "lotes", "equipos", "configuracion"):
            if tabla_esperada in tablas:
                ok(f"Tabla '{tabla_esperada}' existe")
            else:
                err(f"Tabla '{tabla_esperada}' NO existe")
                return False

        # Verificar configuración predeterminada
        cursor.execute("SELECT COUNT(*) FROM configuracion")
        n_config = cursor.fetchone()[0]
        ok(f"Configuración predeterminada: {n_config} claves cargadas")

        # Verificar dataclasses
        m = Mensaje(fecha="2026-01-16", hora="07:15", remitente="Pedro", texto="Prueba")
        ok(f"Dataclass Mensaje: {m}")

        cfg = Configuracion(clave="tamano_lote", valor="50")
        ok(f"Dataclass Configuracion.como_int() = {cfg.como_int()}")

        return True
    except Exception as e:
        err(f"Error en database: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_attachment_detector() -> bool:
    """Verifica la detección de adjuntos en distintos escenarios."""
    titulo("TEST 3: parser/attachment_detector.py")
    from parser.attachment_detector import detectar_adjuntos, tiene_adjuntos

    casos = [
        (
            "IMG-20260116-WA0028.jpg (file attached) foto del rodamiento",
            ["IMG-20260116-WA0028.jpg"],
            False,
            "foto del rodamiento",
        ),
        (
            "(media omitted)",
            [],
            True,
            "",
        ),
        (
            "IMG-001.jpg (file attached) IMG-002.jpg (file attached) evidencia",
            ["IMG-001.jpg", "IMG-002.jpg"],
            False,
            "evidencia",
        ),
        (
            "Texto sin adjuntos ni media",
            [],
            False,
            "Texto sin adjuntos ni media",
        ),
        (
            "reporte.pdf (file attached)",
            ["reporte.pdf"],
            False,
            "",
        ),
    ]

    todos_ok = True
    for texto_entrada, adj_esp, media_esp, texto_esp in casos:
        r = detectar_adjuntos(texto_entrada)
        adj_ok    = r.adjuntos == adj_esp
        media_ok  = r.media_omitida == media_esp
        texto_ok  = r.texto_limpio == texto_esp

        if adj_ok and media_ok and texto_ok:
            ok(f"'{texto_entrada[:45]}...' → adjuntos={r.adjuntos}, media={r.media_omitida}")
        else:
            todos_ok = False
            err(f"Fallo en: '{texto_entrada[:45]}'")
            if not adj_ok:
                err(f"  adjuntos esperados: {adj_esp}, obtenidos: {r.adjuntos}")
            if not media_ok:
                err(f"  media esperada: {media_esp}, obtenida: {r.media_omitida}")
            if not texto_ok:
                err(f"  texto esperado: '{texto_esp}', obtenido: '{r.texto_limpio}'")

    return todos_ok


def test_message_cleaner() -> bool:
    """Verifica que los filtros de ruido descartan los mensajes correctos."""
    titulo("TEST 4: parser/message_cleaner.py")
    from parser.message_cleaner import es_ruido

    casos_ruido = [
        # (remitente, texto, deberia_ser_ruido)
        ("Sistema", "Messages and calls are end-to-end encrypted.", True),
        ("Sistema", "created group", True),
        ("Sistema", "added you", True),
        ("Pedro",   "",                   True),
        ("Pedro",   "   ",                True),
        ("Luis",    "@Maria @Pedro",      True),
        ("Pedro",   "Se cambia rodamiento en prensa #7", False),
        ("Maria",   "Buenos días equipo", False),
        ("Carlos",  "Solicito correa tipo B", False),
    ]

    todos_ok = True
    for remitente, texto, esperado in casos_ruido:
        resultado = es_ruido(remitente, texto)
        estado = "ruido" if resultado else "válido"
        if resultado == esperado:
            ok(f"[{estado}] '{texto[:50]}'")
        else:
            todos_ok = False
            esperado_str = "ruido" if esperado else "válido"
            err(f"Esperaba [{esperado_str}] pero obtuvo [{estado}]: '{texto[:50]}'")

    return todos_ok


def test_normalizacion_fecha_hora() -> bool:
    """Verifica la normalización de fechas y horas."""
    titulo("TEST 5: Normalización de fechas y horas")
    from parser.whatsapp_parser import _normalizar_fecha, _normalizar_hora

    casos_fecha = [
        ("1/16/26",    "2026-01-16"),
        ("16/1/2026",  "2026-01-16"),
        ("12/31/25",   "2025-12-31"),
        ("3/5/26",     "2026-03-05"),
    ]

    casos_hora = [
        ("4:33 PM",  "16:33"),
        ("12:00 PM", "12:00"),
        ("12:00 AM", "00:00"),
        ("7:05 AM",  "07:05"),
        ("16:33",    "16:33"),
        ("9:00 AM",  "09:00"),
    ]

    todos_ok = True

    for raw, esperado in casos_fecha:
        resultado = _normalizar_fecha(raw)
        if resultado == esperado:
            ok(f"Fecha '{raw}' → '{resultado}'")
        else:
            err(f"Fecha '{raw}': esperado '{esperado}', obtenido '{resultado}'")
            todos_ok = False

    for raw, esperado in casos_hora:
        resultado = _normalizar_hora(raw)
        if resultado == esperado:
            ok(f"Hora '{raw}' → '{resultado}'")
        else:
            err(f"Hora '{raw}': esperado '{esperado}', obtenido '{resultado}'")
            todos_ok = False

    return todos_ok


def test_parser_completo(db_path: Path) -> bool:
    """Prueba el parseo completo con el chat de muestra."""
    titulo("TEST 6: Parser completo (parsear_archivo)")
    try:
        from parser.whatsapp_parser import parsear_archivo
        from database import repo_mensajes

        # Crear archivo temporal con el chat de muestra
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as f:
            f.write(CHAT_MUESTRA)
            ruta_tmp = Path(f.name)

        ok(f"Archivo de prueba creado: {ruta_tmp.name}")

        # Parsear
        resumen = parsear_archivo(ruta_tmp, reemplazar=True)
        ok(f"Mensajes cargados:       {resumen.mensajes_cargados}")
        ok(f"Mensajes descartados:    {resumen.mensajes_descartados}")
        ok(f"Con adjuntos:            {resumen.mensajes_con_adjuntos}")
        ok(f"Con media omitida:       {resumen.mensajes_con_media_omitida}")

        if resumen.advertencias:
            for adv in resumen.advertencias:
                warn(f"Advertencia: {adv}")

        # Verificar en BD
        total = repo_mensajes.contar()
        ok(f"Total en BD:             {total}")
        assert total == resumen.mensajes_cargados, (
            f"Mismatch: parseo={resumen.mensajes_cargados}, BD={total}"
        )

        # Verificar algunos mensajes específicos
        mensajes = repo_mensajes.get_all()

        # Verificar mensaje con múltiples adjuntos
        multi_adj = [m for m in mensajes if len(m.adjuntos) == 2]
        if multi_adj:
            ok(f"Mensaje con 2 adjuntos encontrado: {multi_adj[0].adjuntos}")
        else:
            warn("No se encontró mensaje con 2 adjuntos")

        # Verificar mensaje con media omitida
        media_om = [m for m in mensajes if m.media_omitida]
        if media_om:
            ok(f"Mensaje con media_omitida encontrado: '{media_om[0].texto}'")
        else:
            warn("No se encontró mensaje con media_omitida")

        # Verificar líneas de continuación
        multicontinuacion = [m for m in mensajes if "\n" in m.texto]
        if multicontinuacion:
            ok(f"Mensaje con continuación: '{multicontinuacion[0].texto[:60]}'")
        else:
            warn("No se encontró mensaje con línea de continuación")

        # Verificar remitentes únicos
        remitentes = repo_mensajes.get_remitentes_unicos()
        ok(f"Remitentes únicos: {remitentes}")

        # Verificar estadísticas por estado
        por_estado = repo_mensajes.contar_por_estado()
        ok(f"Por estado: {por_estado}")

        # Limpiar archivo temporal
        ruta_tmp.unlink(missing_ok=True)

        return True

    except Exception as e:
        err(f"Error en parser completo: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_repo_crud(db_path: Path) -> bool:
    """Prueba operaciones CRUD del repositorio de mensajes."""
    titulo("TEST 7: CRUD repo_mensajes")
    try:
        from database import repo_mensajes
        from database.models import Mensaje

        # INSERT
        m = Mensaje(
            fecha="2026-01-20",
            hora="10:00",
            remitente="Test Usuario",
            texto="Mensaje de prueba CRUD",
            adjuntos=["foto.jpg"],
        )
        nuevo_id = repo_mensajes.insertar(m)
        ok(f"Insertar: ID asignado = {nuevo_id}")
        assert nuevo_id > 0

        # GET BY ID
        recuperado = repo_mensajes.get_by_id(nuevo_id)
        assert recuperado is not None
        assert recuperado.remitente == "Test Usuario"
        assert recuperado.adjuntos == ["foto.jpg"]
        ok(f"Get by ID: {recuperado}")

        # UPDATE
        recuperado.texto = "Texto modificado"
        recuperado.editado_manual = True
        ok_upd = repo_mensajes.actualizar(recuperado)
        assert ok_upd
        verificado = repo_mensajes.get_by_id(nuevo_id)
        assert verificado is not None
        assert verificado.texto == "Texto modificado"
        assert verificado.editado_manual is True
        ok(f"Actualizar: texto='{verificado.texto}', editado_manual={verificado.editado_manual}")

        # FILTROS
        filtrados = repo_mensajes.get_por_filtros(
            fecha_desde="2026-01-20",
            fecha_hasta="2026-01-20",
            remitente="Test Usuario",
        )
        assert len(filtrados) >= 1
        ok(f"Filtrar: {len(filtrados)} mensajes encontrados")

        # KEYWORD (buscar en el texto actualizado)
        por_keyword = repo_mensajes.get_por_filtros(keyword="modificado")
        assert len(por_keyword) >= 1
        ok(f"Búsqueda por keyword 'modificado': {len(por_keyword)} resultado(s)")

        # DELETE
        eliminado = repo_mensajes.eliminar(nuevo_id)
        assert eliminado
        assert repo_mensajes.get_by_id(nuevo_id) is None
        ok(f"Eliminar ID {nuevo_id}: OK")

        return True

    except Exception as e:
        err(f"Error en CRUD: {e}")
        import traceback
        traceback.print_exc()
        return False


# ---------------------------------------------------------------------------
# Runner principal
# ---------------------------------------------------------------------------

def main() -> None:
    print(f"\n{'='*60}")
    print(" SUITE DE PRUEBAS - ETAPA 1 - PalmaMtto Desktop")
    print(f"{'='*60}")

    # Usar BD temporal para no contaminar la BD real
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = Path(tmp_dir) / "test_palma.db"

        resultados: dict[str, bool] = {}

        resultados["config"]          = test_config()
        resultados["database"]        = test_database(db_path)
        resultados["attachment"]      = test_attachment_detector()
        resultados["cleaner"]         = test_message_cleaner()
        resultados["normalizacion"]   = test_normalizacion_fecha_hora()
        resultados["parser_completo"] = test_parser_completo(db_path)
        resultados["crud"]            = test_repo_crud(db_path)

        # Cerrar BD
        from database.connection import db
        db.close()

    # Resumen final
    titulo("RESUMEN")
    total  = len(resultados)
    ok_cnt = sum(1 for v in resultados.values() if v)
    fail   = total - ok_cnt

    for nombre, resultado in resultados.items():
        if resultado:
            ok(f"{nombre}")
        else:
            err(f"{nombre}")

    print()
    if fail == 0:
        print(f"{C.OK}{C.BOLD}  ✓ Todos los tests pasaron ({ok_cnt}/{total}){C.RESET}")
        print(f"\n  La Etapa 1 está lista. Continúa con la Etapa 2 (interfaz gráfica).")
    else:
        print(f"{C.ERR}{C.BOLD}  ✗ {fail} test(s) fallaron ({ok_cnt}/{total} pasaron){C.RESET}")
        sys.exit(1)

    print()


if __name__ == "__main__":
    main()
