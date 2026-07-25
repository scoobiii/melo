# Localização no repo: tests/unit/test_ai_adapter.py
"""
Testes do packages/ai/adapter.py. Nenhum teste aqui faz chamada de rede
real - requests.post é sempre mockado.
"""

from unittest.mock import MagicMock, patch

import pytest
import requests

from packages.ai.adapter import (
    AdaptationGenerationError,
    AdaptationParseError,
    LyricAdapter,
    _parse_response,
)
from packages.prompts.templates import GenreCorrelation, build_user_prompt

CORRELATION = GenreCorrelation(
    source_genre="tipico_panameno",
    target_genre="pisadinha",
    bpm_source=96.0,
    bpm_target_estimate=130.0,
    correlation_score=0.72,
)

VALID_RESPONSE_XML = """
<analysis>
  <theme>saudade de terra natal</theme>
  <target_meter>fraseado curto, 4 sílabas por linha</target_meter>
</analysis>
<adaptation>
  <lyrics>linha adaptada aqui</lyrics>
  <notes>ajustar para caber no BPM de destino</notes>
</adaptation>
"""


def _mock_response(status_code=200, content=None, text=""):
    resp = MagicMock()
    resp.status_code = status_code
    resp.text = text
    if content is not None:
        resp.json.return_value = {"content": content}
    return resp


def test_build_user_prompt_rejects_empty_lyrics():
    with pytest.raises(ValueError):
        build_user_prompt("", CORRELATION)


def test_build_user_prompt_includes_correlation_fields():
    prompt = build_user_prompt("uma letra qualquer", CORRELATION)
    assert "tipico_panameno" in prompt
    assert "pisadinha" in prompt
    assert "0.72" in prompt


def test_parse_response_happy_path():
    result = _parse_response(VALID_RESPONSE_XML)
    assert result.theme == "saudade de terra natal"
    assert result.lyrics == "linha adaptada aqui"


def test_parse_response_missing_tag_raises():
    broken = "<analysis><theme>x</theme></analysis>"
    with pytest.raises(AdaptationParseError):
        _parse_response(broken)


def test_adapter_requires_api_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(RuntimeError):
        LyricAdapter()


@patch("packages.ai.adapter.requests.post")
def test_adapter_adapt_success(mock_post):
    mock_post.return_value = _mock_response(
        status_code=200,
        content=[{"type": "text", "text": VALID_RESPONSE_XML}],
    )

    adapter = LyricAdapter(api_key="fake-key-for-test")
    result = adapter.adapt("letra original", CORRELATION)

    assert result.theme == "saudade de terra natal"
    mock_post.assert_called_once()


@patch("packages.ai.adapter.time.sleep", return_value=None)
@patch("packages.ai.adapter.requests.post")
def test_adapter_retries_on_5xx_then_raises(mock_post, _mock_sleep):
    mock_post.return_value = _mock_response(status_code=503, text="overloaded")

    adapter = LyricAdapter(api_key="fake-key-for-test", max_retries=2)
    with pytest.raises(AdaptationGenerationError):
        adapter.adapt("letra original", CORRELATION)

    assert mock_post.call_count == 2


@patch("packages.ai.adapter.requests.post")
def test_adapter_does_not_retry_on_401(mock_post):
    mock_post.return_value = _mock_response(status_code=401, text="unauthorized")

    adapter = LyricAdapter(api_key="fake-key-for-test", max_retries=3)
    with pytest.raises(AdaptationGenerationError):
        adapter.adapt("letra original", CORRELATION)

    # 401 não é retryable: só deve ter tentado uma vez
    assert mock_post.call_count == 1


@patch("packages.ai.adapter.time.sleep", return_value=None)
@patch("packages.ai.adapter.requests.post")
def test_adapter_retries_on_network_error(mock_post, _mock_sleep):
    mock_post.side_effect = requests.exceptions.ConnectionError("no network")

    adapter = LyricAdapter(api_key="fake-key-for-test", max_retries=2)
    with pytest.raises(AdaptationGenerationError):
        adapter.adapt("letra original", CORRELATION)

    assert mock_post.call_count == 2
