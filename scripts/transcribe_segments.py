#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# Arquivo         : transcribe_segments.py
# Diretorio       : scripts/
# Responsabilidade: Para cada mix_track do catálogo (um mix_id), extrai o
#                    trecho de áudio correspondente (start/end segundos) via
#                    ffmpeg e transcreve via packages.lyrics.transcriber_cpp
#                    (whisper.cpp local, modelo small por padrão). Grava a
#                    transcrição de volta no mix_track.
# Versao          : 1.0.0
# Data/hora       : 2026-07-26
# Autoria         : MELO / GOS3 - Scrum . Agile . DevOps
# Ciclo de vida   : PERSISTENTE — mantém em scripts/, é ferramenta reutilizável
#                    (qualquer mix novo vai precisar disso), não one-shot.
# -----------------------------------------------------------------------------
"""
Uso (teste pequeno ANTES de rodar tudo — recomendado):
    python scripts/transcribe_segments.py <mix_id> --limit 3

Uso completo (só depois de confirmar que o teste pequeno funcionou):
    python scripts/transcribe_segments.py <mix_id>

Opções:
    --limit N        Processa só os primeiros N segmentos (teste). Sem
                      --limit, processa todos.
    --modelo NOME     Modelo whisper.cpp (default: small)
    --idioma COD      Idioma (default: es — ajuste conforme a faixa)
    --audio-origem P  WAV fonte de onde extrair os segmentos (default:
                      assets/samples/tipico_mix_16k.wav)
    --db-path P       Banco do catálogo (default: melo_catalog.db)
"""
import argparse
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from packages.catalog.store import CatalogStore  # noqa: E402
from packages.lyrics.transcriber_cpp import transcribe_audio  # noqa: E402


def extract_segment(audio_origem: str, inicio: float, fim: float, saida: Path) -> None:
    """Extrai um trecho [inicio, fim) de audio_origem para saida (WAV)."""
    duracao = fim - inicio
    subprocess.run(
        [
            "ffmpeg", "-y", "-loglevel", "error",
            "-i", audio_origem,
            "-ss", str(inicio),
            "-t", str(duracao),
            "-ar", "16000", "-ac", "1",
            str(saida),
        ],
        check=True,
    )


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mix_id", type=int)
    ap.add_argument("--limit", type=int, default=None, help="Processa só os primeiros N segmentos (teste)")
    ap.add_argument("--modelo", default="small")
    ap.add_argument("--idioma", default="es")
    ap.add_argument("--audio-origem", default="assets/samples/tipico_mix_16k.wav")
    ap.add_argument("--db-path", default="melo_catalog.db")
    ap.add_argument("--tmp-dir", default=str(Path.home() / "melo_tmp_segments"))
    args = ap.parse_args()

    store = CatalogStore(db_path=args.db_path)
    tracks = store.list_mix_tracks(args.mix_id)  # assume que este método existe; ajustar se nome real for outro

    if args.limit:
        tracks = tracks[: args.limit]

    tmp_dir = Path(args.tmp_dir)
    tmp_dir.mkdir(parents=True, exist_ok=True)

    print(f"==> Transcrevendo {len(tracks)} segmento(s) do mix_id={args.mix_id} (modelo={args.modelo}, idioma={args.idioma})")
    if args.limit:
        print(f"==> MODO TESTE (--limit {args.limit}) — rode sem --limit depois de confirmar que está ok.")

    inicio_geral = time.time()
    for i, track in enumerate(tracks, 1):
        seg_path = tmp_dir / f"segmento_{track.track_indice}.wav"
        t0 = time.time()
        try:
            extract_segment(args.audio_origem, track.inicio_segundos, track.fim_segundos or (track.inicio_segundos + 30), seg_path)
            texto = transcribe_audio(str(seg_path), modelo=args.modelo, idioma=args.idioma)
        except Exception as exc:  # noqa: BLE001
            print(f"  [{i}/{len(tracks)}] indice={track.track_indice} FALHOU: {exc}")
            continue

        store.update_mix_track_transcricao(args.mix_id, track.track_indice, texto)
        dt = time.time() - t0
        print(f"  [{i}/{len(tracks)}] indice={track.track_indice} ({dt:.1f}s): {texto[:60]!r}")

    total = time.time() - inicio_geral
    print(f"==> Concluído: {len(tracks)} segmento(s) em {total:.1f}s ({total/max(len(tracks),1):.1f}s/segmento em média)")
    if not args.limit:
        print("==> Nada mais a fazer manualmente — resultados já gravados no catálogo.")


if __name__ == "__main__":
    main()
