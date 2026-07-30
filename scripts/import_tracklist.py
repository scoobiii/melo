#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# Arquivo         : import_tracklist.py
# Diretorio       : scripts/
# Responsabilidade:
#   Importa um tracklist curado (formato exportado de ferramentas tipo
#   AI Studio/Gemini: {title, videoUrl, segments:[{artist, startTime,
#   endTime, text}]}) para o catalogo MELO via CatalogStore.
#
#   NAO baixa audio, NAO acessa rede, NAO chama YouTube. So le um JSON local
#   e grava no SQLite via add_mix/add_mix_track/identify_mix_track. Isso e
#   deliberado: curadoria de metadados (quem canta o que, em que trecho) e
#   dado estrutural, diferente de extracao de audio de plataforma de
#   streaming, que o README do projeto proibe.
#
#   fingerprint_servico e marcado como "curadoria_manual" (nao e resultado
#   de fingerprinting acustico tipo AudD/ACRCloud) - honesto sobre a origem
#   do dado: alguem (humano ou IA assistindo o video) identificou, nao um
#   algoritmo de reconhecimento de audio.
# Versao          : 1.0.0
# Data/hora       : 2026-07-29
# Autoria         : MELO / GOS3 - Scrum . Agile . DevOps
# -----------------------------------------------------------------------------
"""
Uso:
    python3 scripts/import_tracklist.py \
        --json melo-transcription-1785367803211.json \
        --dj "DJ Phantom Panama" \
        --genero-origem tipico_panameno \
        --db melo_catalog.db
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from packages.catalog.store import CatalogStore

FINGERPRINT_SERVICO = "curadoria_manual"
CONFIANCA_COM_ARTISTA = 1.0
CONFIANCA_SO_TITULO = 0.5  # titulo identificado mas artista desconhecido


def _parse_tempo(timestr: str) -> float:
    """Converte HH:MM:SS ou MM:SS para segundos."""
    partes = [int(p) for p in timestr.split(":")]
    if len(partes) == 3:
        h, m, s = partes
        return h * 3600 + m * 60 + s
    if len(partes) == 2:
        m, s = partes
        return m * 60 + s
    return float(partes[0])


def _parse_artista_titulo(campo: str) -> tuple[str | None, str]:
    """'Arielis Nicole - Y Llorarás e Sufrirás' -> ('Arielis Nicole', 'Y Llorarás e Sufrirás')
    'Recuerdo que Mata' (sem separador) -> (None, 'Recuerdo que Mata')
    """
    if " - " in campo:
        artista, titulo = campo.split(" - ", 1)
        return artista.strip(), titulo.strip()
    return None, campo.strip()


def importar(json_path: Path, dj_nome: str, genero_origem: str, db_path: str) -> None:
    data = json.loads(json_path.read_text(encoding="utf-8"))
    segments = data.get("segments", [])
    video_url = data.get("videoUrl", str(json_path))

    catalog = CatalogStore(db_path)

    mix_id = catalog.add_mix(dj_nome=dj_nome, arquivo_path=video_url)
    print(f"==> Mix registrado (id={mix_id}): {data.get('title', '?')}")

    identificados = 0
    so_titulo = 0

    for i, seg in enumerate(segments):
        inicio = _parse_tempo(seg["startTime"])
        fim = _parse_tempo(seg["endTime"]) if seg.get("endTime") else None

        mix_track_id = catalog.add_mix_track(
            mix_id=mix_id, track_indice=i, inicio_segundos=inicio, fim_segundos=fim,
        )

        artista, titulo = _parse_artista_titulo(seg.get("artist", ""))

        source_artist_id = None
        confianca = CONFIANCA_SO_TITULO
        if artista:
            source_artist_id = catalog.add_source_artist(
                nome=artista, genero_origem=genero_origem, faixa_original=titulo,
            )
            confianca = CONFIANCA_COM_ARTISTA
            identificados += 1
        else:
            so_titulo += 1

        catalog.identify_mix_track(
            mix_track_id=mix_track_id,
            titulo_identificado=titulo,
            fingerprint_servico=FINGERPRINT_SERVICO,
            fingerprint_confianca=confianca,
            source_artist_id=source_artist_id,
        )

        artista_display = artista or "(artista desconhecido)"
        print(f"  [{i}] {seg['startTime']}-{seg['endTime']} | {artista_display} — {titulo}")

    print(f"\n==> {len(segments)} trechos importados: "
          f"{identificados} com artista identificado, {so_titulo} só com título.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", required=True, type=Path)
    parser.add_argument("--dj", required=True, help="Nome do DJ/curador do mix")
    parser.add_argument("--genero-origem", default="tipico_panameno")
    parser.add_argument("--db", default="melo_catalog.db")
    args = parser.parse_args()

    if not args.json.exists():
        print(f"Arquivo não encontrado: {args.json}", file=sys.stderr)
        sys.exit(1)

    importar(args.json, args.dj, args.genero_origem, args.db)


if __name__ == "__main__":
    main()
