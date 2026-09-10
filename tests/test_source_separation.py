from pathlib import Path

import pytest

from packages.separation.demucs import separate_vocals_instrumental


def test_missing_input_is_rejected(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        separate_vocals_instrumental(tmp_path / "missing.wav", tmp_path / "out")


def test_invalid_options_are_rejected(tmp_path: Path):
    src = tmp_path / "input.wav"
    src.write_bytes(b"audio")

    with pytest.raises(ValueError, match="shifts"):
        separate_vocals_instrumental(src, tmp_path / "out", shifts=0)

    with pytest.raises(ValueError, match="segment"):
        separate_vocals_instrumental(src, tmp_path / "out", segment=0)


def test_backend_arguments_and_outputs(tmp_path: Path, monkeypatch):
    src = tmp_path / "mix.wav"
    src.write_bytes(b"audio")
    out = tmp_path / "out"
    backend = tmp_path / "backend"
    (backend / "htdemucs" / "mix").mkdir(parents=True)
    (backend / "htdemucs" / "mix" / "vocals.wav").write_bytes(b"vocal")
    (backend / "htdemucs" / "mix" / "no_vocals.wav").write_bytes(b"instrumental")

    calls = {}

    class FakeDemucs:
        @staticmethod
        def main(argv):
            calls["argv"] = argv
            # O backend real escreveria em --out. O fake copia os artefatos
            # para simular o contrato necessário ao adapter.
            out_index = argv.index("--out") + 1
            target = Path(argv[out_index]) / "htdemucs" / "mix"
            target.mkdir(parents=True, exist_ok=True)
            for name in ("vocals.wav", "no_vocals.wav"):
                target.joinpath(name).write_bytes(
                    (backend / "htdemucs" / "mix" / name).read_bytes()
                )

    monkeypatch.setitem(__import__("sys").modules, "demucs", type("M", (), {})())
    monkeypatch.setitem(__import__("sys").modules, "demucs.separate", FakeDemucs)

    result = separate_vocals_instrumental(
        src, out, model="htdemucs", device="cpu", segment=10, shifts=2
    )

    assert calls["argv"][:8] == [
        "--two-stems", "vocals", "-n", "htdemucs", "-d", "cpu",
        "--out", str(out.resolve()),
    ]
    assert "--segment" in calls["argv"]
    assert calls["argv"][-1] == str(src.resolve())
    assert result.vocal_path.read_bytes() == b"vocal"
    assert result.instrumental_path.read_bytes() == b"instrumental"
