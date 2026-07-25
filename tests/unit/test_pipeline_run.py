import sys
import types

import numpy as np
import pytest
import soundfile as sf

from packages.pipeline.run import run_pipeline


class _FakeSegment:
    def __init__(self, text):
        self.text = text


class _FakeInfo:
    language = "pt"


class _FakeModel:
    def __init__(self, *args, **kwargs):
        pass

    def transcribe(self, path, language=None, **kwargs):
        segments = [_FakeSegment("letra falsa de teste")]
        return segments, _FakeInfo()


@pytest.fixture
def fake_whisper(monkeypatch):
    fake_module = types.ModuleType("faster_whisper")
    fake_module.WhisperModel = _FakeModel
    monkeypatch.setitem(sys.modules, "faster_whisper", fake_module)
    return fake_module


@pytest.fixture
def sample_wav(tmp_path):
    """Trilha real (WAV) com um pulso periódico, pra exercitar audio+adaptation de verdade."""
    sample_rate = 22050
    duration = 4.0
    bpm = 100
    n_samples = int(sample_rate * duration)
    y = np.zeros(n_samples)
    interval = int(sample_rate * 60.0 / bpm)
    for i in range(0, n_samples, interval):
        y[i:i + 50] = 0.8

    path = tmp_path / "faixa_teste.wav"
    sf.write(str(path), y, sample_rate)
    return str(path)


def test_run_pipeline_with_transcription(sample_wav, fake_whisper):
    resultado = run_pipeline(sample_wav, genero_origem="tipico_panameno")

    assert resultado.duration_seconds == pytest.approx(4.0, abs=0.05)
    assert resultado.sample_rate == 22050
    assert resultado.bpm > 0
    assert len(resultado.correlacoes) > 0
    assert resultado.transcricao == "letra falsa de teste"
    assert resultado.transcricao_erro is None


def test_run_pipeline_without_whisper_installed_degrades_gracefully(sample_wav, monkeypatch):
    # garante que 'whisper' NÃO está disponível, simulando ambiente sem o pacote
    monkeypatch.setitem(sys.modules, "whisper", None)

    resultado = run_pipeline(sample_wav, genero_origem="cumbia_panamena")

    assert resultado.bpm > 0  # pipeline continua funcionando
    assert len(resultado.correlacoes) > 0
    assert resultado.transcricao is None
    assert resultado.transcricao_erro is not None


def test_run_pipeline_skips_transcription_when_disabled(sample_wav):
    resultado = run_pipeline(sample_wav, genero_origem="tamborito", transcrever=False)

    assert resultado.transcricao is None
    assert resultado.transcricao_erro is None


def test_pipeline_result_to_dict_is_json_serializable(sample_wav, fake_whisper):
    import json

    resultado = run_pipeline(sample_wav, genero_origem="tipico_panameno")
    serializado = json.dumps(resultado.to_dict(), ensure_ascii=False)
    assert "tipico_panameno" in serializado
