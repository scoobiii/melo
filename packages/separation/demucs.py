#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# Arquivo        : demucs.py
# Diretório      : packages/separation/
# Responsabilidade:
#   Separa áudio musical em VOCAL e INSTRUMENTAL usando Demucs. A camada MELO
#   encapsula o backend para que o restante do pipeline não dependa da CLI.
# Versão         : 1.0.0
# Data/hora      : 2026-09-10
# Autoria        : MELO / GOS3 — Scrum · Agile · DevOps
# -----------------------------------------------------------------------------
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence
import importlib


@dataclass(frozen=True)
class SeparationResult:
    """Artefatos produzidos pela separação de duas fontes."""

    input_path: Path
    vocal_path: Path
    instrumental_path: Path
    model: str
    device: str


def _validate_input(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Áudio não encontrado: {path}")
    if not path.is_file():
        raise ValueError(f"Entrada não é arquivo: {path}")
    if path.stat().st_size == 0:
        raise ValueError(f"Áudio vazio: {path}")


def _find_stems(root: Path, model: str, stem_name: str, track_stem: str) -> Path:
    candidates = list(root.glob(f"**/{stem_name}.wav"))
    if not candidates:
        raise RuntimeError(
            f"Demucs terminou sem produzir {stem_name}.wav para {track_stem!r} "
            f"(modelo={model}, diretório={root})"
        )
    # Demucs normalmente produz exatamente um stem para cada entrada. Ordenar
    # torna a seleção determinística caso o backend crie diretórios auxiliares.
    return sorted(candidates)[0]


def separate_vocals_instrumental(
    input_path: str | Path,
    output_dir: str | Path,
    *,
    model: str = "htdemucs",
    device: str = "cpu",
    segment: float | None = None,
    shifts: int = 1,
) -> SeparationResult:
    """Produz VOCAL.wav e INSTRUMENTAL.wav a partir de um mix.

    A operação usa o modo `--two-stems vocals` do Demucs. O backend ainda
    calcula a separação completa e deriva o acompanhamento como a soma das
    fontes não-vocais; isso evita tratar "instrumental" como simples remoção
    espectral da voz.

    Args:
        input_path: WAV/MP3/etc. aceito pelo backend.
        output_dir: diretório final dos dois artefatos MELO.
        model: modelo Demucs, por padrão `htdemucs`.
        device: `cpu`, `cuda` ou outro dispositivo aceito pelo Demucs.
        segment: tamanho do bloco em segundos; útil para reduzir RAM/VRAM.
        shifts: número de deslocamentos para ensemble; 1 é determinístico e
            econômico, valores maiores aumentam qualidade potencial e custo.
    """
    src = Path(input_path).expanduser().resolve()
    out = Path(output_dir).expanduser().resolve()
    _validate_input(src)
    if shifts < 1:
        raise ValueError("shifts deve ser >= 1")
    if segment is not None and segment <= 0:
        raise ValueError("segment deve ser > 0")

    try:
        demucs_separate = importlib.import_module("demucs.separate")
    except ImportError as exc:
        raise RuntimeError(
            "Dependência opcional ausente. Instale com: pip install demucs"
        ) from exc

    out.mkdir(parents=True, exist_ok=True)
    argv: list[str] = [
        "--two-stems", "vocals",
        "-n", model,
        "-d", device,
        "--out", str(out),
        "--shifts", str(shifts),
    ]
    if segment is not None:
        argv.extend(["--segment", str(segment)])
    argv.append(str(src))

    # A API pública do Demucs recebe os mesmos argumentos da CLI. Evitamos
    # shell=True/subprocess para não introduzir parsing de shell no pipeline.
    demucs_separate.main(argv)

    track_stem = src.stem
    backend_vocal = _find_stems(out, model, "vocals", track_stem)
    backend_other = _find_stems(out, model, "no_vocals", track_stem)

    vocal = out / f"{track_stem}_VOCAL.wav"
    instrumental = out / f"{track_stem}_INSTRUMENTAL.wav"
    if vocal.resolve() != backend_vocal.resolve():
        vocal.write_bytes(backend_vocal.read_bytes())
    if instrumental.resolve() != backend_other.resolve():
        instrumental.write_bytes(backend_other.read_bytes())

    return SeparationResult(
        input_path=src,
        vocal_path=vocal,
        instrumental_path=instrumental,
        model=model,
        device=device,
    )
