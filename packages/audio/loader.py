"""Minimal audio loading and metadata extraction."""
from dataclasses import dataclass
from pathlib import Path

import soundfile as sf


@dataclass
class AudioInfo:
    path: str
    duration_seconds: float
    sample_rate: int
    channels: int
    frames: int


def load_audio_info(path: str) -> AudioInfo:
    """Read audio file metadata without loading full sample data into memory."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Audio file not found: {path}")

    with sf.SoundFile(str(p)) as f:
        return AudioInfo(
            path=str(p),
            duration_seconds=len(f) / f.samplerate,
            sample_rate=f.samplerate,
            channels=f.channels,
            frames=len(f),
        )
