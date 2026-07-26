# packages/voices/generator.py
"""
Geração/regravação de áudio adaptado (Fase 1).

Status: esqueleto funcional + stubs de integração.
- Instrumental: placeholder (time-stretch + EQ leve via scipy/numpy).
- Voz: exige modelo externo (RVC / Coqui / Bark / API paga).
  NUNCA clonar artista real sem licença explícita (ver README legal).

Quando um backend real for plugado, só trocar o método _synthesize_*.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np
from scipy import signal

logger = logging.getLogger("melo.voices.generator")


class VoiceGenerationError(Exception):
    """Falha definitiva na geração de áudio."""


@dataclass(frozen=True)
class GeneratedTrack:
    path: str
    duration_seconds: float
    sample_rate: int
    bpm_target: float
    source_genre: str
    target_genre: str
    notes: str


class InstrumentalAdapter:
    """Adaptação instrumental mínima (time-stretch + filtro de textura).

    Não é geração generativa — só prepara o áudio original para o BPM/textura
    do gênero-alvo. Suficiente para protótipo até ter modelo real.
    """

    def adapt(
        self,
        audio_path: str,
        target_bpm: float,
        source_bpm: float,
        output_path: str,
        source_genre: str = "",
        target_genre: str = "",
        texture: str = "acordeon_dancante",
    ) -> GeneratedTrack:
        import soundfile as sf

        y, sr = sf.read(audio_path, always_2d=False)
        if y.ndim > 1:
            y = y.mean(axis=1)

        ratio = target_bpm / max(source_bpm, 1.0)
        n_out = int(len(y) / ratio)
        y_stretched = signal.resample(y, n_out)

        if "percussivo" in texture:
            b, a = signal.butter(2, 120 / (sr / 2), btype="high")
            y_stretched = signal.filtfilt(b, a, y_stretched)
        elif "romantico" in texture:
            b, a = signal.butter(2, 4000 / (sr / 2), btype="low")
            y_stretched = signal.filtfilt(b, a, y_stretched)

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        sf.write(output_path, y_stretched.astype(np.float32), sr)

        return GeneratedTrack(
            path=output_path,
            duration_seconds=len(y_stretched) / sr,
            sample_rate=sr,
            bpm_target=target_bpm,
            source_genre=source_genre,
            target_genre=target_genre,
            notes=f"Instrumental time-stretched {source_bpm:.1f}→{target_bpm:.1f} bpm (placeholder)",
        )


class VoiceGenerator:
    """Gerador de voz / regravação.

    Backend padrão = None (levanta erro claro).
    Para produção: injetar callable que recebe (lyrics, target_genre, ref_audio)
    e devolve path do WAV gerado.
    """

    def __init__(self, backend=None):
        self._backend = backend

    def generate(
        self,
        lyrics: str,
        target_genre: str,
        bpm: float,
        output_path: str,
        reference_audio: Optional[str] = None,
    ) -> GeneratedTrack:
        if self._backend is None:
            raise VoiceGenerationError(
                "Nenhum backend de voz configurado. "
                "Instale RVC/Coqui/Bark ou passe backend=callable no construtor. "
                "Clonagem de artista real exige licença explícita."
            )
        path = self._backend(
            lyrics=lyrics,
            target_genre=target_genre,
            bpm=bpm,
            output_path=output_path,
            reference_audio=reference_audio,
        )
        import soundfile as sf
        info = sf.info(path)
        return GeneratedTrack(
            path=path,
            duration_seconds=info.duration,
            sample_rate=info.samplerate,
            bpm_target=bpm,
            source_genre="",
            target_genre=target_genre,
            notes="Gerado por backend injetado",
        )
