import sys
import types

import pytest

from packages.lyrics.transcriber import transcribe_and_save, transcribe_audio


class _FakeModel:
    def transcribe(self, path, language=None, verbose=False):
        return {"text": f"  texto transcrito de {path} ({language})  "}


@pytest.fixture
def fake_whisper(monkeypatch):
    """Injeta um módulo 'whisper' falso em sys.modules, sem precisar do pacote real instalado."""
    fake_module = types.ModuleType("whisper")
    fake_module.load_model = lambda modelo: _FakeModel()
    monkeypatch.setitem(sys.modules, "whisper", fake_module)
    return fake_module


@pytest.fixture
def sample_audio(tmp_path):
    p = tmp_path / "musica.mp3"
    p.write_bytes(b"fake-mp3-bytes")
    return str(p)


def test_transcribe_audio_returns_stripped_text(sample_audio, fake_whisper):
    texto = transcribe_audio(sample_audio, modelo="small", idioma="pt")
    assert texto == f"texto transcrito de {sample_audio} (pt)"


def test_transcribe_audio_raises_on_missing_file(fake_whisper):
    with pytest.raises(FileNotFoundError):
        transcribe_audio("nao_existe.mp3")


def test_transcribe_audio_raises_on_invalid_model(sample_audio):
    with pytest.raises(ValueError):
        transcribe_audio(sample_audio, modelo="gigante")


def test_transcribe_and_save_writes_file(sample_audio, fake_whisper, tmp_path):
    saida = tmp_path / "letra.txt"
    resultado = transcribe_and_save(sample_audio, saida=str(saida))
    assert resultado == saida
    assert saida.read_text(encoding="utf-8") == f"texto transcrito de {sample_audio} (pt)"
