#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# Arquivo        : separate_vocals.py
# Diretório      : scripts/
# Responsabilidade: CLI MELO para produzir vocal e instrumental de um áudio.
# Versão         : 1.0.0
# Data/hora      : 2026-09-10
# Autoria        : MELO / GOS3 — Scrum · Agile · DevOps
# -----------------------------------------------------------------------------
from __future__ import annotations

import argparse

from packages.separation.demucs import separate_vocals_instrumental


def main() -> None:
    parser = argparse.ArgumentParser(
        description="MELO: separa um mix em VOCAL e INSTRUMENTAL usando Demucs."
    )
    parser.add_argument("audio", help="Arquivo de áudio de entrada")
    parser.add_argument(
        "--out", default="output/separation", help="Diretório dos artefatos"
    )
    parser.add_argument("--model", default="htdemucs", help="Modelo Demucs")
    parser.add_argument(
        "--device", default="cpu", help="Dispositivo Demucs: cpu/cuda"
    )
    parser.add_argument(
        "--segment", type=float, default=None,
        help="Tamanho do segmento em segundos; use para reduzir RAM/VRAM",
    )
    parser.add_argument(
        "--shifts", type=int, default=1,
        help="Número de shifts do ensemble; 1 é o modo econômico",
    )
    args = parser.parse_args()

    result = separate_vocals_instrumental(
        args.audio,
        args.out,
        model=args.model,
        device=args.device,
        segment=args.segment,
        shifts=args.shifts,
    )
    print(f"VOCAL       : {result.vocal_path}")
    print(f"INSTRUMENTAL: {result.instrumental_path}")
    print(f"MODEL       : {result.model}")
    print(f"DEVICE      : {result.device}")


if __name__ == "__main__":
    main()
