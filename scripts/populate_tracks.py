#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# Arquivo         : populate_tracks.py
# Diretorio       : scripts/
# Responsabilidade: Le um JSON de segmentos (saida de detect_track_boundaries.py
#                    ou de full_mix_analysis.py) e insere cada segmento como
#                    mix_track no catalogo (packages.catalog.store.CatalogStore).
#                    Nao identifica artista - so popula os segmentos brutos,
#                    todos como 'nao_identificado', pra revisao manual/posterior.
# Versao          : 2.0.0 (generalizado — v1.0.0 tinha MIX_ID e caminho de
#                    JSON hardcoded, corrigido pra reuso com múltiplos mixes)
# Data/hora       : 2026-07-26
# Autoria         : MELO / GOS3 - Scrum . Agile . DevOps
# -----------------------------------------------------------------------------
"""
Uso:
    python scripts/populate_tracks.py <mix_id> <json_path> \
        [--db-path melo_catalog.db]

Exemplo:
    python scripts/populate_tracks.py 1 output/tipico_mix_vol2_dj_phantom.json
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from packages.catalog.store import CatalogStore  # noqa: E402


def populate_tracks(mix_id: int, json_path: str, db_path: str = "melo_catalog.db") -> int:
    """Insere os segmentos de `json_path` como mix_tracks do `mix_id` no catálogo.

    Returns:
        Número de segmentos inseridos com sucesso.

    Raises:
        FileNotFoundError: se json_path não existir.
        ValueError: se o JSON não for uma lista não-vazia.
    """
    caminho = Path(json_path)
    if not caminho.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {json_path}")

    segments = json.loads(caminho.read_text(encoding="utf-8"))
    if not isinstance(segments, list) or not segments:
        raise ValueError(f"JSON vazio ou formato inesperado em {json_path}")

    store = CatalogStore(db_path=db_path)

    inseridos = 0
    for seg in segments:
        indice = seg.get("indice") if "indice" in seg else seg.get("faixa_candidata")
        inicio = seg.get("start_sec")
        fim = seg.get("end_sec")

        if indice is None or inicio is None:
            print(f"  [aviso] segmento sem indice/inicio, pulando: {seg}")
            continue

        store.add_mix_track(
            mix_id,
            track_indice=indice,
            inicio_segundos=float(inicio),
            fim_segundos=float(fim) if fim is not None else None,
        )
        inseridos += 1

    return inseridos


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mix_id", type=int, help="ID do mix já cadastrado no catálogo")
    ap.add_argument("json_path", help="Caminho do JSON de segmentos")
    ap.add_argument("--db-path", default="melo_catalog.db", help="Caminho do banco SQLite (default: melo_catalog.db)")
    args = ap.parse_args()

    inseridos = populate_tracks(args.mix_id, args.json_path, args.db_path)
    print(f"OK: {inseridos} segmentos inseridos no catalog (mix_id={args.mix_id}).")
    print("Todos 'nao_identificado' — nenhum artist/beneficiary/royalty_pct atribuído.")


if __name__ == "__main__":
    main()
