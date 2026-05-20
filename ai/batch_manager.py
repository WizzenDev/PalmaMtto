"""
ai/batch_manager.py
-------------------
Gestion de lotes y procesamiento IA.
"""

import time
from datetime import datetime
from typing import Optional

from ai.openai_client import OpenAIClient
from ai.prompt_builder import construir_prompt
from config import MAX_REINTENTOS_IA
from database.models import Equipo
import database.repo_equipos as repo_equipos
import database.repo_lotes as repo_lotes
import database.repo_mensajes as repo_mensajes
import database.repo_config as repo_config


class BatchManager:
    """Gestiona la division y procesamiento de lotes de IA."""

    def __init__(self) -> None:
        self._pausa = repo_config.get_int("pausa_entre_lotes", 1)
        self._tamano = repo_config.get_int("tamano_lote", 50)

    def generar_lotes(self) -> list[list[int]]:
        """Retorna una lista de lotes logicos (listas de ids)."""
        mensajes = repo_mensajes.get_sin_procesar()
        ids = [m.id for m in mensajes if m.id is not None]
        lotes: list[list[int]] = []
        for i in range(0, len(ids), self._tamano):
            lotes.append(ids[i : i + self._tamano])
        return lotes

    def procesar_lote(self, ids: list[int]) -> int:
        """Procesa un lote y retorna el id de lote creado en BD."""
        if not ids:
            return 0

        proveedor = repo_config.get_str("proveedor_ia", "openai")
        prompt_base = repo_config.get_str("prompt_base", "")
        api_key = repo_config.get_str("api_key_openai", "")
        modelo = repo_config.get_str("modelo_openai", "gpt-4o-mini")
        agregar_equipos = repo_config.get_bool("agregar_equipos_automatico", True)

        mensajes = [repo_mensajes.get_by_id(i) for i in ids]
        mensajes_validos = [m for m in mensajes if m is not None]

        lote_id = repo_lotes.insertar_lote(
            numero_lote=repo_lotes.siguiente_numero_lote(),
            id_primer_mensaje=ids[0],
            id_ultimo_mensaje=ids[-1],
            cantidad=len(ids),
            proveedor=proveedor,
        )

        if proveedor != "openai":
            repo_lotes.actualizar_error(lote_id, "Proveedor no implementado")
            return lote_id

        if not api_key:
            repo_lotes.actualizar_error(lote_id, "API key de OpenAI vacia")
            return lote_id

        equipos = [e.nombre for e in repo_equipos.get_all(include_inactivos=False)]
        payload = [{"id": m.id, "texto": m.texto} for m in mensajes_validos]
        prompt = construir_prompt(prompt_base, equipos, payload)

        client = OpenAIClient(api_key=api_key, model=modelo)

        resultado: Optional[list[dict]] = None
        for intento in range(MAX_REINTENTOS_IA + 1):
            try:
                resultado = client.classify_batch(payload, equipos, prompt)
                break
            except ValueError:
                if intento >= MAX_REINTENTOS_IA:
                    repo_lotes.actualizar_error(lote_id, "JSON invalido en respuesta")
                    return lote_id
            except ConnectionError as exc:
                repo_lotes.actualizar_error(lote_id, str(exc))
                return lote_id

        if resultado is None:
            repo_lotes.actualizar_error(lote_id, "Respuesta vacia")
            return lote_id

        ahora = datetime.now().isoformat(timespec="seconds")

        for item in resultado:
            msg_id = item.get("id")
            equipo = item.get("equipo")
            tipo = item.get("tipo_mensaje")
            if msg_id is None or tipo is None:
                continue

            if equipo and agregar_equipos:
                if not repo_equipos.get_by_nombre(equipo):
                    repo_equipos.insertar(
                        Equipo(
                            nombre=equipo,
                            descripcion=None,
                            activo=True,
                            origen="ia_sugerido",
                        )
                    )

            repo_mensajes.actualizar_clasificacion_ia(
                id_mensaje=int(msg_id),
                equipo=equipo,
                tipo_mensaje=tipo,
                id_lote=lote_id,
                fecha_proceso=ahora,
            )

        repo_lotes.actualizar_procesado(lote_id, tokens_usados=None)
        return lote_id

    def procesar_lotes(self, lotes: list[list[int]], on_progress=None) -> None:
        """Procesa varios lotes con pausa configurada."""
        total = len(lotes)
        for idx, lote in enumerate(lotes, start=1):
            self.procesar_lote(lote)
            if on_progress:
                on_progress(idx, total)
            time.sleep(self._pausa)
