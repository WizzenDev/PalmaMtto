"""
ai/openai_client.py
-------------------
Cliente OpenAI (Chat Completions) usando httpx.
"""

import json
from typing import Any

import httpx

from ai.base_client import AIClient


class OpenAIClient(AIClient):
    """Cliente OpenAI para clasificacion de mensajes."""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini") -> None:
        self._api_key = api_key
        self._model = model
        self._url = "https://api.openai.com/v1/chat/completions"

    def classify_batch(
        self,
        messages: list[dict],
        equipment_list: list[str],
        prompt_base: str,
    ) -> list[dict]:
        prompt = prompt_base
        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": "Responde solo JSON valido."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
        }

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        try:
            with httpx.Client(timeout=60) as client:
                resp = client.post(self._url, headers=headers, json=payload)
        except httpx.RequestError as exc:
            raise ConnectionError(str(exc)) from exc

        if resp.status_code != 200:
            raise ConnectionError(f"OpenAI error {resp.status_code}: {resp.text}")

        data: dict[str, Any] = resp.json()
        contenido = data["choices"][0]["message"]["content"]

        try:
            resultado = json.loads(contenido)
        except json.JSONDecodeError as exc:
            raise ValueError("Respuesta no es JSON valido") from exc

        if not isinstance(resultado, list):
            raise ValueError("Respuesta no es una lista JSON")

        return resultado
