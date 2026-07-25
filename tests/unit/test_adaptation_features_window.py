import numpy as np
import pytest
import soundfile as sf

from packages.adaptation.features import extract_features


def _long_click_track(bpm: float, sample_rate: int = 22050, duration: float = 180.0) -> np.ndarray:
    """Simula um arquivo longo (3 min) — tempo homogêneo, só pra validar que a
    janela central é lida corretamente e não o arquivo inteiro."""
    n_samples = int(sample_rate * duration)
    y = np.zeros(n_samples)
    interval = int(sample_rate * 60.0 / bpm)
    for i in range(0, n_samples, interval):
        y[i:i + 50] = 0.8
    return y


@pytest.fixture
def long_audio_file(tmp_path):
    sample_rate = 22050
    y = _long_click_track(110.0, sample_rate=sample_rate, duration=180.0)
    path = tmp_path / "faixa_longa.wav"
    sf.write(str(path), y, sample_rate)
    return str(path)


def test_extract_features_reads_only_the_window(long_audio_file):
    resultado = extract_features(long_audio_file, window_seconds=30.0)
    # a janela lida deve ser ~30s, não os 180s totais do arquivo
    assert resultado.window_seconds == pytest.approx(30.0, abs=0.1)


def test_extract_features_defaults_to_center_of_file(long_audio_file):
    resultado = extract_features(long_audio_file, window_seconds=30.0)
    # centro de um arquivo de 180s com janela de 30s: offset ~75s
    assert resultado.window_offset_seconds == pytest.approx(75.0, abs=0.5)


def test_extract_features_respects_custom_offset(long_audio_file):
    resultado = extract_features(long_audio_file, window_seconds=20.0, offset_seconds=10.0)
    assert resultado.window_offset_seconds == pytest.approx(10.0, abs=0.01)
    assert resultado.window_seconds == pytest.approx(20.0, abs=0.1)


def test_extract_features_bpm_still_correct_on_windowed_read(long_audio_file):
    resultado = extract_features(long_audio_file, window_seconds=30.0)
    candidatos = [110.0, 55.0, 220.0]
    assert any(abs(resultado.bpm - c) / c < 0.08 for c in candidatos)


def test_extract_features_raises_when_offset_exceeds_duration(long_audio_file):
    with pytest.raises(ValueError, match="Janela inválida"):
        extract_features(long_audio_file, window_seconds=10.0, offset_seconds=999.0)


def test_extract_features_downmixes_stereo_to_mono(tmp_path):
    sample_rate = 22050
    duration = 10.0
    bpm = 100
    n_samples = int(sample_rate * duration)
    y_mono = np.zeros(n_samples)
    interval = int(sample_rate * 60.0 / bpm)
    for i in range(0, n_samples, interval):
        y_mono[i:i + 50] = 0.8

    y_stereo = np.column_stack([y_mono, np.roll(y_mono, 5)])
    path = tmp_path / "faixa_estereo.wav"
    sf.write(str(path), y_stereo, sample_rate)

    resultado = extract_features(str(path), window_seconds=8.0, offset_seconds=0.0)
    assert resultado.bpm > 0
