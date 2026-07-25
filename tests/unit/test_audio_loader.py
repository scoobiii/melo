import numpy as np
import pytest
import soundfile as sf

from packages.audio.loader import load_audio_info


@pytest.fixture
def sample_wav(tmp_path):
    """Generate a 1-second 440Hz sine wave as a real WAV fixture."""
    sample_rate = 44100
    duration = 1.0
    freq = 440.0
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    data = 0.5 * np.sin(2 * np.pi * freq * t)

    path = tmp_path / "test_tone.wav"
    sf.write(str(path), data, sample_rate)
    return str(path)


def test_load_audio_info_returns_correct_metadata(sample_wav):
    info = load_audio_info(sample_wav)
    assert info.sample_rate == 44100
    assert info.channels == 1
    assert abs(info.duration_seconds - 1.0) < 0.01


def test_load_audio_info_raises_on_missing_file():
    with pytest.raises(FileNotFoundError):
        load_audio_info("nonexistent_file.wav")
