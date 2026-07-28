#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# Arquivo         : prepare_wer_eval.py
# Diretorio       : scripts/
# Responsabilidade: Extrai N segmentos de áudio (via ffmpeg) e gera um
#                    template de texto (um bloco por segmento) pra você
#                    preencher com a transcrição REAL que ouviu — ground
#                    truth pra depois calcular WER contra o que o
#                    whisper.cpp produziu.
# Versao          : 1.0.0
# Data/hora       : 2026-07-27
# Autoria         : MELO / GOS3 - Scrum . Agile . DevOps
# Ciclo de vida   : PERSISTENTE — ferramenta de avaliação de qualidade,
#                    mantém em scripts/. Sem input() bloqueante — roda até
#                    o fim sozinho, você preenche o template depois, offline.
# -----------------------------------------------------------------------------
"""
Uso:
    python scripts/prepare_wer_eval.py <mix_id> --n-amostras 10

Gera:
    output/wer_eval/segmento_<indice>.wav       (áudio de cada amostra)
    output/wer_eval/transcricoes_whisper.json   (o que o whisper.cpp já produziu)
    output/wer_eval/template_ground_truth.txt   (você preenche isso ouvindo)

Depois de preencher o template, rode:
    python scripts/compute_wer.py
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from packages.catalog.store import CatalogStore  # noqa: E402

OUT_DIR = Path("output/wer_eval")


def extract_segment(audio_origem: str, inicio: float, fim: float, saida: Path) -> None:
    subprocess.run(
        [
            "ffmpeg", "-y", "-loglevel", "error",
            "-i", audio_origem,
            "-ss", str(inicio), "-t", str(fim - inicio),
            "-ar", "16000", "-ac", "1",
            str(saida),
        ],
        check=True,
    )


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mix_id", type=int)
    ap.add_argument("--n-amostras", type=int, default=10, help="Quantos segmentos amostrar (default: 10)")
    ap.add_argument("--audio-origem", default="assets/samples/tipico_mix_16k.wav")
    ap.add_argument("--db-path", default="melo_catalog.db")
    args = ap.parse_args()

    store = CatalogStore(db_path=args.db_path)
    tracks = store.list_tracks_for_mix(args.mix_id)

    com_transcricao = [t for t in tracks if getattr(t, "transcricao", None)]
    if not com_transcricao:
        print("Nenhum segmento com transcrição encontrado — rode transcribe_segments.py antes.")
        sys.exit(1)

    # amostragem espaçada (não só os primeiros N — pega distribuição ao longo do mix)
    passo = max(1, len(com_transcricao) // args.n_amostras)
    amostra = com_transcricao[::passo][: args.n_amostras]

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    transcricoes_whisper = {}
    linhas_template = []

    print(f"==> Extraindo {len(amostra)} amostra(s) de {len(com_transcricao)} segmento(s) transcritos")

    for track in amostra:
        seg_path = OUT_DIR / f"segmento_{track.track_indice}.wav"
        fim = track.fim_segundos or (track.inicio_segundos + 30)
        extract_segment(args.audio_origem, track.inicio_segundos, fim, seg_path)
        transcricoes_whisper[track.track_indice] = track.transcricao
        linhas_template.append(
            f"# segmento {track.track_indice} — arquivo: {seg_path.name}\n"
            f"# whisper disse: {track.transcricao!r}\n"
            f"GROUND_TRUTH_{track.track_indice}: \n"
        )
        print(f"  extraído: {seg_path}")

    (OUT_DIR / "transcricoes_whisper.json").write_text(
        json.dumps(transcricoes_whisper, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (OUT_DIR / "template_ground_truth.txt").write_text(
        "\n".join(linhas_template), encoding="utf-8"
    )

    print("")
    print(f"==> Ouça cada .wav em {OUT_DIR}/ e preencha:")
    print(f"    {OUT_DIR}/template_ground_truth.txt")
    print("==> Escreva o texto real depois de cada 'GROUND_TRUTH_N: ', uma linha por segmento.")
    print("==> Depois rode: python scripts/compute_wer.py")


if __name__ == "__main__":
    main()
