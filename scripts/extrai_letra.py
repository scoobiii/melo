#!/usr/bin/env python3
"""
extrai_letra.py — transcreve áudio de MP3 usando Whisper (local, sem API)
Uso: python extrai_letra.py musica.mp3 [--modelo base|small|medium|large]
"""
import argparse
import sys
from pathlib import Path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("arquivo", help="Caminho do MP3")
    parser.add_argument("--modelo", default="small",
                         choices=["tiny", "base", "small", "medium", "large"])
    parser.add_argument("--idioma", default="pt", help="Código do idioma (pt, en, etc)")
    parser.add_argument("--saida", default=None, help="Arquivo .txt de saída")
    args = parser.parse_args()

    import whisper  # pip install openai-whisper

    caminho = Path(args.arquivo)
    if not caminho.exists():
        sys.exit(f"Arquivo não encontrado: {caminho}")

    print(f"Carregando modelo Whisper '{args.modelo}'...")
    model = whisper.load_model(args.modelo)

    print("Transcrevendo...")
    resultado = model.transcribe(str(caminho), language=args.idioma, verbose=False)

    texto = resultado["text"].strip()
    saida = args.saida or caminho.with_suffix(".txt")
    Path(saida).write_text(texto, encoding="utf-8")

    print(f"\n--- Transcrição ---\n{texto}\n")
    print(f"Salvo em: {saida}")

if __name__ == "__main__":
    main()
