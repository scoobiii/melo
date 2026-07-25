# Localização no repo: packages/ai/adapter.py
"""
Cliente de geração de adaptação de letra via Anthropic API.

Implementado com `requests` puro (HTTP direto ao endpoint /v1/messages),
em vez do SDK oficial `anthropic`. Motivo: o SDK depende de `jiter`, que
exige compilar uma extensão Rust nativa; o target aarch64-linux-android
(Termux) não tem toolchain Rust suportada pelo rustup para esse triple,
então `pip install anthropic` falha nesse ambiente. `requests` já é
dependência de requirements/base.txt e não tem esse problema.

Padrão seguido (senior devops):
- configuração via variável de ambiente, nunca hardcoded
- timeout e retry explícitos, com backoff
- logging estruturado (não print) - nível INFO para operação normal,
  WARNING para retry, ERROR para falha definitiva
- exceções tipadas próprias, para o chamador não precisar tratar
  exceções genéricas de HTTP
- parsing de saída XML delimitada, tolerante a variação de whitespace
  mas explícito sobre o que fazer se o formato vier quebrado (falha, não
  adivinha)

Dependência: requests (já presente em requirements/base.txt).
"""

from __future__ import annotations

import logging
import os
import re
import time
from dataclasses import dataclass

import requests

from packages.prompts.templates import (
    SYSTEM_PROMPT,
    GenreCorrelation,
    build_user_prompt,
)

logger = logging.getLogger("melo.ai.adapter")

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_API_VERSION = "2023-06-01"
DEFAULT_MODEL = "claude-sonnet-4-6"
DEFAULT_TIMEOUT_SECONDS = 30.0
DEFAULT_MAX_RETRIES = 3
_RETRY_BACKOFF_BASE_SECONDS = 2.0
# Códigos HTTP que valem retry (transitórios). 4xx de erro de request
# (400, 401, 403, 404) não devem ter retry - falhariam de novo do mesmo jeito.
_RETRYABLE_STATUS_CODES = {408, 429, 500, 502, 503, 504}


class AdaptationGenerationError(Exception):
    """Erro definitivo (após esgotar retries) ao gerar adaptação."""


class AdaptationParseError(Exception):
    """A API respondeu, mas fora do formato XML esperado."""


@dataclass(frozen=True)
class LyricAdaptation:
    theme: str
    target_meter: str
    lyrics: str
    notes: str


def _extract_tag(text: str, tag: str) -> str:
    match = re.search(rf"<{tag}>(.*?)</{tag}>", text, re.DOTALL)
    if not match:
        raise AdaptationParseError(
            f"Tag <{tag}> não encontrada na resposta do modelo"
        )
    return match.group(1).strip()


def _parse_response(raw_text: str) -> LyricAdaptation:
    try:
        return LyricAdaptation(
            theme=_extract_tag(raw_text, "theme"),
            target_meter=_extract_tag(raw_text, "target_meter"),
            lyrics=_extract_tag(raw_text, "lyrics"),
            notes=_extract_tag(raw_text, "notes"),
        )
    except AdaptationParseError:
        logger.error(
            "Falha ao parsear resposta do modelo. Primeiros 200 chars: %r",
            raw_text[:200],
        )
        raise


class LyricAdapter:
    """Cliente de alto nível para gerar adaptação de letra entre gêneros.

    Uso:
        adapter = LyricAdapter()
        result = adapter.adapt(letra_original, correlation)
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str = DEFAULT_MODEL,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        max_retries: int = DEFAULT_MAX_RETRIES,
    ) -> None:
        # Nunca aceitar API key hardcoded no código chamador - só via env
        # ou injeção explícita em teste.
        resolved_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not resolved_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY não definida. Configure a variável de "
                "ambiente ou passe api_key explicitamente (uso recomendado "
                "apenas em teste)."
            )
        self._api_key = resolved_key
        self._model = model
        self._timeout_seconds = timeout_seconds
        self._max_retries = max_retries

    def adapt(
        self,
        original_lyrics: str,
        correlation: GenreCorrelation,
    ) -> LyricAdaptation:
        user_prompt = build_user_prompt(original_lyrics, correlation)
        headers = {
            "x-api-key": self._api_key,
            "anthropic-version": ANTHROPIC_API_VERSION,
            "content-type": "application/json",
        }
        payload = {
            "model": self._model,
            "max_tokens": 1024,
            "system": SYSTEM_PROMPT,
            "messages": [{"role": "user", "content": user_prompt}],
        }

        last_error: Exception | None = None
        for attempt in range(1, self._max_retries + 1):
            try:
                logger.info(
                    "Gerando adaptação %s->%s (tentativa %d/%d)",
                    correlation.source_genre,
                    correlation.target_genre,
                    attempt,
                    self._max_retries,
                )
                response = requests.post(
                    ANTHROPIC_API_URL,
                    headers=headers,
                    json=payload,
                    timeout=self._timeout_seconds,
                )

                if response.status_code == 200:
                    data = response.json()
                    raw_text = "".join(
                        block.get("text", "")
                        for block in data.get("content", [])
                        if block.get("type") == "text"
                    )
                    return _parse_response(raw_text)

                if response.status_code in _RETRYABLE_STATUS_CODES:
                    last_error = RuntimeError(
                        f"HTTP {response.status_code}: {response.text[:200]}"
                    )
                    logger.warning(
                        "Tentativa %d/%d falhou com HTTP %d",
                        attempt,
                        self._max_retries,
                        response.status_code,
                    )
                    if attempt < self._max_retries:
                        time.sleep(_RETRY_BACKOFF_BASE_SECONDS * attempt)
                    continue

                # Erro não-retryable (ex: 400, 401, 403) - falha rápido.
                raise AdaptationGenerationError(
                    f"HTTP {response.status_code} não recuperável: "
                    f"{response.text[:200]}"
                )

            except AdaptationParseError:
                raise

            except AdaptationGenerationError:
                raise

            except requests.exceptions.RequestException as exc:
                last_error = exc
                logger.warning(
                    "Tentativa %d/%d falhou: %s", attempt, self._max_retries, exc
                )
                if attempt < self._max_retries:
                    time.sleep(_RETRY_BACKOFF_BASE_SECONDS * attempt)

        logger.error(
            "Esgotadas %d tentativas de geração de adaptação", self._max_retries
        )
        raise AdaptationGenerationError(
            f"Falha ao gerar adaptação após {self._max_retries} tentativas"
        ) from last_error
