#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# Arquivo        : merge_tracklist_into_whisper.py
# Diretorio      : scripts/
# Responsabilidade:
#   Copia identificacao de artista/titulo da tracklist curada manualmente
#   (mix_id=2, poucos segmentos grandes) para os segmentos finos gerados
#   pelo Whisper (mix_id=1, 190 segmentos), casando por sobreposicao de
#   intervalo de tempo. Nao apaga nada do mix 1 - so preenche
#   source_artist_id/titulo_identificado/status/fingerprint quando o
#   segmento cai dentro do intervalo de uma faixa oficial.
# Versao         : 1.0.0
# Data/hora      : 2026-07-28
# Autoria        : MELO / GOS3 - Scrum . Agile . DevOps
# -----------------------------------------------------------------------------
"""
Uso:
    # sempre rodar --dry-run primeiro, conferir o log, so depois --apply
    python scripts/merge_tracklist_into_whisper.py --db melo_catalog.db --dry-run
    python scripts/merge_tracklist_into_whisper.py --db melo_catalog.db --apply
"""
import argparse
import sqlite3
from pathlib import Path


def fmt_time(sec):
    m, s = divmod(int(sec), 60)
    return f"{m}m{s:02d}s"


def load_tracks(conn, mix_id):
    cur = conn.execute(
        """SELECT id, track_indice, inicio_segundos, fim_segundos,
                  status_identificacao, titulo_identificado, source_artist_id,
                  fingerprint_servico, fingerprint_confianca
           FROM mix_tracks WHERE mix_id = ? ORDER BY inicio_segundos""",
        (mix_id,),
    )
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def find_overlapping_official(whisper_start, whisper_end, official_tracks):
    """Retorna a faixa oficial cujo intervalo contem o segmento do whisper,
    ou None se nenhuma cobrir. whisper_end pode ser None (ultimo segmento)."""
    w_end = whisper_end if whisper_end is not None else whisper_start + 1
    for off in official_tracks:
        o_start = off["inicio_segundos"]
        o_end = off["fim_segundos"] if off["fim_segundos"] is not None else float("inf")
        if whisper_start >= o_start and w_end <= o_end + 0.5:
            return off
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--db", required=True)
    ap.add_argument("--whisper-mix-id", type=int, default=1)
    ap.add_argument("--official-mix-id", type=int, default=2)
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--dry-run", action="store_true", help="so mostra o que faria, nao grava")
    group.add_argument("--apply", action="store_true", help="grava de verdade no banco")
    args = ap.parse_args()

    if not Path(args.db).exists():
        raise SystemExit(f"banco nao encontrado: {args.db}")

    conn = sqlite3.connect(args.db)
    whisper_tracks = load_tracks(conn, args.whisper_mix_id)
    official_tracks = load_tracks(conn, args.official_mix_id)

    print(f"==> {len(whisper_tracks)} segmentos whisper (mix_id={args.whisper_mix_id})")
    print(f"==> {len(official_tracks)} faixas oficiais (mix_id={args.official_mix_id})")

    matches = []
    for w in whisper_tracks:
        official = find_overlapping_official(
            w["inicio_segundos"], w["fim_segundos"], official_tracks
        )
        if official is not None and official["source_artist_id"] is not None:
            matches.append((w, official))

    print(f"\n==> {len(matches)} segmentos whisper serao vinculados a faixa oficial:\n")
    for w, official in matches:
        print(
            f"  whisper[{w['track_indice']}] {fmt_time(w['inicio_segundos'])} "
            f"-> oficial: {official['titulo_identificado']} "
            f"(source_artist_id={official['source_artist_id']}, "
            f"confianca={official['fingerprint_confianca']})"
        )

    if args.dry_run:
        print(f"\n==> DRY-RUN: nada foi gravado. Rode com --apply para persistir.")
        conn.close()
        return

    for w, official in matches:
        conn.execute(
            """UPDATE mix_tracks SET
                   source_artist_id = ?,
                   titulo_identificado = ?,
                   status_identificacao = ?,
                   fingerprint_servico = 'curadoria_manual_via_tracklist',
                   fingerprint_confianca = ?
               WHERE id = ?""",
            (
                official["source_artist_id"],
                official["titulo_identificado"],
                official["status_identificacao"],
                official["fingerprint_confianca"],
                w["id"],
            ),
        )
    conn.commit()
    conn.close()
    print(f"\n==> {len(matches)} segmentos atualizados no banco.")


if __name__ == "__main__":
    main()
