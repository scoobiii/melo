"""Extração leve de features de áudio (BPM) sem dependências pesadas.

Evita librosa/numba de propósito (build instável em Termux/Android ARM64).
Usa apenas numpy/scipy sobre o envelope de onset via autocorrelação.

IMPORTANTE: analisa uma JANELA CURTA do áudio (default 40s, a partir do
centro do arquivo), não o arquivo inteiro. BPM não é um conceito estável
sobre faixas longas ou mixes com múltiplas músicas — analisar o arquivo
inteiro produz picos espúrios de autocorrelação sem significado musical.
Para mixes/playlists com várias faixas, o ideal é segmentar por faixa
antes de estimar BPM (fora do escopo deste módulo).
"""
from dataclasses import dataclass
from typing import Optional

import numpy as np
from scipy.signal import correlate


@dataclass
class AudioFeatures:
    bpm: float
    sample_rate: int
    window_seconds: float
    window_offset_seconds: float


def _onset_envelope(y: np.ndarray, frame_len: int = 1024, hop: int = 512) -> np.ndarray:
    n_frames = max(0, (len(y) - frame_len) // hop)
    rms = np.array([
        np.sqrt(np.mean(y[i * hop: i * hop + frame_len] ** 2))
        for i in range(n_frames)
    ])
    onset = np.diff(rms)
    onset[onset < 0] = 0
    return onset


def estimate_bpm(
    y: np.ndarray,
    sample_rate: int,
    min_bpm: float = 60.0,
    max_bpm: float = 200.0,
    hop: int = 512,
) -> float:
    """Estima BPM via autocorrelação do envelope de onset.

    Método aproximado — suficiente para correlação de gênero, não para
    quantização rítmica precisa. Espera receber um trecho curto e
    homogêneo (uma faixa, ou um recorte dela), não um arquivo longo
    com múltiplas músicas.
    """
    onset = _onset_envelope(y, hop=hop)
    if len(onset) < 2:
        raise ValueError("Áudio curto demais para estimar BPM")
    if np.max(onset) <= 1e-9:
        raise ValueError("Nenhum onset detectado (áudio silencioso ou sem transientes)")

    ac = correlate(onset, onset, mode="full")
    ac = ac[len(ac) // 2:]

    sr_frames = sample_rate / hop
    min_lag = max(1, int(sr_frames * 60 / max_bpm))
    max_lag = min(len(ac) - 1, int(sr_frames * 60 / min_bpm))
    if max_lag <= min_lag:
        raise ValueError("Janela de BPM inválida para a duração do áudio")

    peak_lag = int(np.argmax(ac[min_lag:max_lag])) + min_lag
    bpm = 60.0 * sr_frames / peak_lag
    return round(bpm, 1)


def extract_features(
    path: str,
    window_seconds: float = 40.0,
    offset_seconds: Optional[float] = None,
) -> AudioFeatures:
    """Carrega uma JANELA do arquivo de áudio e extrai features básicas (BPM).

    Por padrão, lê `window_seconds` segundos a partir do centro do arquivo
    (evita intro/outro silenciosos e amortiza o efeito de o áudio ser um
    mix longo com múltiplas faixas). Passe `offset_seconds` para escolher
    manualmente o ponto de início da janela.
    """
    import soundfile as sf

    info = sf.info(path)
    duracao_total = info.frames / info.samplerate

    if offset_seconds is None:
        offset_seconds = max(0.0, (duracao_total / 2.0) - (window_seconds / 2.0))

    frame_inicio = int(offset_seconds * info.samplerate)
    frames_janela = int(window_seconds * info.samplerate)
    frames_janela = min(frames_janela, info.frames - frame_inicio)

    if frames_janela <= 0:
        raise ValueError(
            f"Janela inválida: offset {offset_seconds}s excede a duração do áudio ({duracao_total:.1f}s)"
        )

    y, sr = sf.read(path, start=frame_inicio, frames=frames_janela, always_2d=False)
    if y.ndim > 1:
        y = y.mean(axis=1)  # downmix pra mono

    bpm = estimate_bpm(y, sr)
    return AudioFeatures(
        bpm=bpm,
        sample_rate=sr,
        window_seconds=round(frames_janela / sr, 2),
        window_offset_seconds=round(offset_seconds, 2),
    )
