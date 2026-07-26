# Localização no repo: packages/adaptation/mix_segmentation.py
# -----------------------------------------------------------------------------
# Arquivo        : mix_segmentation.py
# Diretório      : packages/adaptation/
# Responsabilidade:
#   Segmentação determinística de ÁUDIO de mix longo em trechos temporais
#   (novelty: RMS + centroide + onset). Não segmenta letra.
# Versão         : 1.0.0
# Data/hora      : 2026-07-26 10:53:29 UTC
# Autoria        : MELO / GOS3 — Scrum · Agile · DevOps
# -----------------------------------------------------------------------------
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import numpy as np
import soundfile as sf

from packages.adaptation.features import estimate_bpm


@dataclass(frozen=True)
class AudioMixSegment:
    indice: int
    start_sec: float
    end_sec: float
    duration_sec: float
    bpm: Optional[float]
    rms_mean: float
    centroid_mean_hz: float


def _envelope_features(y, sr, hop=512, frame=2048):
    n = max(1, (len(y) - frame) // hop)
    rms = np.empty(n)
    cents = np.empty(n)
    window = np.hanning(frame)
    for i in range(n):
        seg = y[i * hop : i * hop + frame]
        rms[i] = np.sqrt(np.mean(seg ** 2) + 1e-12)
        spec = np.abs(np.fft.rfft(seg * window)) + 1e-12
        freqs = np.fft.rfftfreq(frame, 1.0 / sr)
        cents[i] = float((freqs * spec).sum() / spec.sum())
    times = np.arange(n) * hop / sr
    onset = np.diff(rms, prepend=rms[0])
    onset[onset < 0] = 0.0
    return times, rms, cents, onset


def _novelty_score(rms, cents, onset):
    def z(x):
        return (x - np.mean(x)) / (np.std(x) + 1e-9)
    jump_c = np.abs(np.diff(cents, prepend=cents[0]))
    jump_r = np.abs(np.diff(rms, prepend=rms[0]))
    return z(jump_c) + 1.5 * z(jump_r) + 2.0 * z(onset)


def segment_audio_mix(
    path: str,
    min_seg_sec: float = 45.0,
    max_segments: int = 12,
    hop: int = 512,
    frame: int = 2048,
    novelty_k: float = 2.0,
) -> List[AudioMixSegment]:
    y, sr = sf.read(path, always_2d=False)
    if getattr(y, "ndim", 1) > 1:
        y = y.mean(axis=1)
    duration = len(y) / float(sr)
    if duration < 5.0:
        raise ValueError(f"Áudio curto demais ({duration:.2f}s)")

    times, rms, cents, onset = _envelope_features(y, sr, hop, frame)
    score = _novelty_score(rms, cents, onset)
    thr = float(np.median(score) + novelty_k * np.std(score))

    raw = [0.0]
    for i, s in enumerate(score):
        t = float(times[i])
        if s > thr and (t - raw[-1]) >= min_seg_sec * 0.5:
            raw.append(t)
    if duration - raw[-1] > 1.0:
        raw.append(duration)

    merged = [raw[0]]
    for t in raw[1:]:
        if t - merged[-1] < min_seg_sec and t != raw[-1]:
            continue
        merged.append(t)
    if merged[-1] < duration - 0.5:
        merged.append(duration)

    floor = min(5.0, max(2.0, min_seg_sec * 0.5))
    segments: List[AudioMixSegment] = []
    for a, b in zip(merged[:-1], merged[1:]):
        if (b - a) < floor:
            continue
        ia, ib = int(a * sr), int(b * sr)
        try:
            bpm = float(estimate_bpm(y[ia:ib], sr))
        except Exception:
            bpm = None
        i0 = max(0, int(a * sr / hop))
        i1 = min(len(rms), max(i0 + 1, int(b * sr / hop)))
        segments.append(
            AudioMixSegment(
                len(segments), round(a, 2), round(b, 2), round(b - a, 2),
                bpm, round(float(np.mean(rms[i0:i1])), 5),
                round(float(np.mean(cents[i0:i1])), 1),
            )
        )

    if not segments:
        try:
            bpm = float(estimate_bpm(y, sr))
        except Exception:
            bpm = None
        segments = [
            AudioMixSegment(0, 0.0, round(duration, 2), round(duration, 2),
                            bpm, round(float(np.mean(rms)), 5),
                            round(float(np.mean(cents)), 1))
        ]

    if len(segments) > max_segments:
        segments = sorted(segments, key=lambda s: s.duration_sec, reverse=True)[:max_segments]
        segments = sorted(segments, key=lambda s: s.start_sec)
        segments = [
            AudioMixSegment(i, s.start_sec, s.end_sec, s.duration_sec,
                            s.bpm, s.rms_mean, s.centroid_mean_hz)
            for i, s in enumerate(segments)
        ]
    return segments
