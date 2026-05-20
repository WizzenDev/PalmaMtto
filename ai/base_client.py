"""
ai/base_client.py
-----------------
Clase base abstracta para proveedores de IA.
"""

from abc import ABC, abstractmethod


class AIClient(ABC):
    """Interfaz base para clientes de IA."""

    @abstractmethod
    def classify_batch(
        self,
        messages: list[dict],
        equipment_list: list[str],
        prompt_base: str,
    ) -> list[dict]:
        """
        Clasifica un lote de mensajes.

        Retorna lista de dicts con: id, equipo, tipo_mensaje.
        Lanza ConnectionError si no hay internet.
        Lanza ValueError si la respuesta no es JSON valido.
        """
        raise NotImplementedError
