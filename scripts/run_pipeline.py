#!/usr/bin/env python3
"""
run_pipeline.py — demo mínima ponta-a-ponta: audio -> lyrics -> adaptation

Uso:
    python scripts/run_pipeline.py caminho/faixa.mp3 --genero tipico_panameno
    python scripts/run_pipeline.py caminho/faixa.wav --genero cumbia_panamena --sem-transcricao
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from packages.pipeline.run import run_pipeline  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description="Roda o pipeline MELO sobre um arquivo de áudio real.")
    parser.add_argument("arquivo", help="Caminho do áudio (mp3/wav/etc)")
    parser.add_argument(
        "--genero", required=True,
        help="Gênero de origem: tipico_panameno | cumbia_panamena | tamborito",
    )
    parser.add_argument("--modelo", default="small", help="Modelo Whisper (tiny/base/small/medium/large)")
    parser.add_argument("--idioma", default="pt", help="Idioma alvo da transcrição")
    parser.add_argument("--sem-transcricao", action="store_true", help="Pula a etapa de transcrição")
    parser.add_argument("--saida", default=None, help="Caminho do .json de saída (default: output/<nome>_pipeline.json)")
    args = parser.parse_args()

    resultado = run_pipeline(
        args.arquivo,
        genero_origem=args.genero,
        modelo_whisper=args.modelo,
        idioma=args.idioma,
        transcrever=not args.sem_transcricao,
    )

    print(f"\n=== MELO Pipeline: {args.arquivo} ===")
    print(f"Duração: {resultado.duration_seconds:.1f}s | Sample rate: {resultado.sample_rate} | Canais: {resultado.channels}")
    print(f"BPM estimado: {resultado.bpm}")
    print(f"Gênero de origem: {resultado.genero_origem}")
    print("\nCorrelações sugeridas (Brasil):")
    for nome, score in resultado.correlacoes:
        print(f"  - {nome}: {score}")

    if resultado.transcricao:
        print(f"\nTranscrição:\n{resultado.transcricao}")
    elif resultado.transcricao_erro:
        print(f"\n[Transcrição indisponível] {resultado.transcricao_erro}")

    saida = Path(args.saida) if args.saida else Path("output") / f"{Path(args.arquivo).stem}_pipeline.json"
    saida.parent.mkdir(parents=True, exist_ok=True)
    saida.write_text(json.dumps(resultado.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nRelatório salvo em: {saida}")


if __name__ == "__main__":
    main()
