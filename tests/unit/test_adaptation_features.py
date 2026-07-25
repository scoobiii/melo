import numpy as np
import pytest

from packages.adaptation.features import estimate_bpm


def _click_track(bpm: float, sample_rate: int = 22050, duration: float = 8.0) -> np.ndarray:
    """Gera uma trilha de cliques (impulsos) num BPM conhecido, pra validar a estimativa."""
    n_samples = int(sample_rate * duration)
    y = np.zeros(n_samples)
    interval = int(sample_rate * 60.0 / bpm)
    for i in range(0, n_samples, interval):
        y[i:i + 50] = 1.0  # pulso curto
    return y


@pytest.mark.parametrize("bpm_alvo", [90.0, 120.0])
def test_estimate_bpm_recovers_click_track_tempo(bpm_alvo):
    sample_rate = 22050
    y = _click_track(bpm_alvo, sample_rate=sample_rate)
    estimado = estimate_bpm(y, sample_rate)

    # tolera erro de oitava (bpm, bpm/2, bpm*2) e margem de ~8%
    candidatos = [bpm_alvo, bpm_alvo / 2, bpm_alvo * 2]
    assert any(abs(estimado - c) / c < 0.08 for c in candidatos)


def test_estimate_bpm_raises_on_silence():
    y = np.zeros(22050 * 2)
    with pytest.raises(ValueError):
        estimate_bpm(y, 22050)


def test_estimate_bpm_raises_on_very_short_onset_envelope():
    # y curto o bastante para que o envelope de onset tenha menos de 2
    # amostras (frame_len=1024, hop=512 -> precisa de poucos frames).
    y = np.zeros(2000)
    with pytest.raises(ValueError, match="curto demais"):
        estimate_bpm(y, sample_rate=22050)


def test_estimate_bpm_raises_when_bpm_window_invalid_for_short_audio():
    # Áudio com energia real (não silêncio), mas curto o suficiente para
    # que a janela de lags válidos (min_lag..max_lag) colapse.
    rng = np.random.RandomState(42)
    y = rng.rand(4200)  # onset resultante tem ~5 amostras -> max_lag <= min_lag
    with pytest.raises(ValueError, match="Janela de BPM inválida"):
        estimate_bpm(y, sample_rate=22050)
