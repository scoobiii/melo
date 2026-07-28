#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# Arquivo: scripts/verify_transcription_accuracy.py
# Responsabilidade:
#   Amostra N segmentos já transcritos, toca cada um via ffplay, pede pro
#   usuário digitar o que ouviu de verdade, e calcula WER real no final.
#   Salva resultado em JSON -- auditável, não é número solto sem rastro.
#
# Uso:
#   python3 scripts/verify_transcription_accuracy.py \
#       output/tipico_mix_vol2_dj_phantom.json \
#       assets/samples/dj_phantom.wav \
#       --n 10
# -----------------------------------------------------------------------------
import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from packages.lyrics.transcription_accuracy import (  # noqa: E402
    amostrar_segmentos_para_verificacao,
    calcular_wer_medio,
    word_error_rate,
)


import shutil
import tempfile


def tocar_segmento(audio_path: str, start_sec: float, end_sec: float) -> None:
    """Corta o trecho com ffmpeg (sempre disponível, já usado no projeto) e
    toca via termux-media-player (Termux:API) se existir; senão, corta pra
    um arquivo temporário e pede pro usuário abrir manualmente -- ffplay
    não vem com o pacote ffmpeg padrão do Termux (precisa de SDL2)."""
    duracao = end_sec - start_sec
    tmp_dir = Path(__import__("os").environ.get("TMPDIR", str(Path.home() / "melo_tmp")))
    tmp_dir.mkdir(parents=True, exist_ok=True)
    clip_path = tmp_dir / "verify_clip.wav"

    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", audio_path,
         "-ss", str(start_sec), "-t", str(duracao), str(clip_path)],
        check=True,
    )

    if shutil.which("termux-media-player"):
        subprocess.run(["termux-media-player", "play", str(clip_path)])
        input("Tocando via termux-media-player. Pressione Enter quando terminar de ouvir...")
        subprocess.run(["termux-media-player", "stop"], capture_output=True)
    else:
        print(f"ffplay/termux-media-player indisponíveis. Arquivo cortado em:")
        print(f"  {clip_path}")
        print("Abra manualmente (gerenciador de arquivos, ou 'termux-open "
              f"{clip_path}' se o Termux:API estiver instalado).")
        input("Pressione Enter quando terminar de ouvir...")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("json_segmentos")
    ap.add_argument("audio_original")
    ap.add_argument("--n", type=int, default=10)
    ap.add_argument("--out", default="output/verificacao_wer.json")
    args = ap.parse_args()

    segmentos = json.loads(Path(args.json_segmentos).read_text(encoding="utf-8"))
    amostra = amostrar_segmentos_para_verificacao(segmentos, n=args.n)

    if not amostra:
        print("Nenhum segmento com transcrição não-vazia encontrado.")
        sys.exit(1)

    print(f"Amostra de {len(amostra)} segmentos. Pra cada um: ouça, digite o que")
    print("realmente foi dito/cantado. Enter vazio = pular (não entra na média).")
    print("Digite 'sair' a qualquer momento pra parar e calcular com o que já tem.\n")

    pares = []
    detalhes = []

    for i, seg in enumerate(amostra, 1):
        print(f"\n--- Segmento {i}/{len(amostra)} (índice {seg.indice}, "
              f"{seg.start_sec:.0f}s-{seg.end_sec:.0f}s) ---")
        print(f"Whisper transcreveu: {seg.transcricao_whisper}")
        tocar_segmento(args.audio_original, seg.start_sec, seg.end_sec)

        referencia = input("O que você ouviu de verdade? ").strip()
        if referencia.lower() == "sair":
            break
        if not referencia:
            print("(pulado)")
            continue

        wer = word_error_rate(referencia, seg.transcricao_whisper)
        print(f"WER deste segmento: {wer:.3f}")
        pares.append((referencia, seg.transcricao_whisper))
        detalhes.append({
            "indice": seg.indice,
            "start_sec": seg.start_sec,
            "end_sec": seg.end_sec,
            "whisper": seg.transcricao_whisper,
            "referencia_humana": referencia,
            "wer": round(wer, 3),
        })

    if not pares:
        print("\nNenhum segmento verificado. Nada a calcular.")
        sys.exit(0)

    resultado = calcular_wer_medio(pares)
    resultado["detalhes"] = detalhes
    resultado["gerado_em"] = datetime.now(timezone.utc).isoformat()
    resultado["fonte_json"] = args.json_segmentos

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(resultado, ensure_ascii=False, indent=2))

    print("\n" + "=" * 60)
    print(f"WER médio: {resultado['wer_medio']:.3f} "
          f"(0.0=perfeito, 1.0=errou tudo, >1.0=alucinou mais que disse)")
    print(f"WER min/max: {resultado['wer_min']:.3f} / {resultado['wer_max']:.3f}")
    print(f"Baseado em {resultado['n_amostras']} segmentos verificados de verdade")
    print(f"Salvo em {args.out}")


if __name__ == "__main__":
    main()
