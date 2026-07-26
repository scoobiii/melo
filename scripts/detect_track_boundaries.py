#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# Arquivo        : detect_track_boundaries.py
# Diretorio      : scripts/
# Responsabilidade:
#   Agrupa segmentos de full_mix_analysis.py em "faixas candidatas" por
#   plato de BPM sustentado. NAO identifica artista - so organiza os
#   segmentos em blocos revisaveis manualmente (ver docs/MIX_ANALYSIS.md).
# Versao         : 1.0.0
# Data/hora      : 2026-07-26
# Autoria        : MELO / GOS3 - Scrum . Agile . DevOps
# -----------------------------------------------------------------------------
"""
Uso:
    python scripts/detect_track_boundaries.py output/mix_analise.json \
        --out output/mix_faixas_candidatas.json --bpm-tolerance 8 --min-run 2
"""
import argparse
import json
from pathlib import Path


def group_by_bpm_plateau(segments, bpm_tolerance=8.0, min_run=2):
    if not segments:
        return []
    groups = []
    current = [segments[0]]
    for seg in segments[1:]:
        ref_bpm = current[-1].get("bpm")
        seg_bpm = seg.get("bpm")
        if ref_bpm is not None and seg_bpm is not None and abs(seg_bpm - ref_bpm) <= bpm_tolerance:
            current.append(seg)
        else:
            groups.append(current)
            current = [seg]
    groups.append(current)
    merged = []
    for g in groups:
        if merged and len(g) < min_run:
            merged[-1].extend(g)
        else:
            merged.append(g)
    return merged


def summarize_group(group, idx):
    bpms = [s.get("bpm") for s in group if s.get("bpm") is not None]
    lyrics_sample = " / ".join((s.get("transcricao") or "")[:60] for s in group[:3])
    return {
        "faixa_candidata": idx,
        "start_sec": group[0].get("start_sec"),
        "end_sec": group[-1].get("end_sec"),
        "duration_sec": round(group[-1].get("end_sec", 0) - group[0].get("start_sec", 0), 2),
        "n_segmentos": len(group),
        "bpm_medio": round(sum(bpms) / len(bpms), 1) if bpms else None,
        "bpm_min": min(bpms) if bpms else None,
        "bpm_max": max(bpms) if bpms else None,
        "amostra_letra": lyrics_sample,
        "artist": None,
        "work": None,
        "label": None,
        "beneficiary": None,
        "royalty_pct": None,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("json_path")
    ap.add_argument("--out", required=True)
    ap.add_argument("--bpm-tolerance", type=float, default=8.0)
    ap.add_argument("--min-run", type=int, default=2)
    args = ap.parse_args()

    data = json.loads(Path(args.json_path).read_text(encoding="utf-8"))
    segments = data if isinstance(data, list) else data.get("segments", [])

    groups = group_by_bpm_plateau(segments, args.bpm_tolerance, args.min_run)
    faixas = [summarize_group(g, i) for i, g in enumerate(groups)]

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(faixas, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"==> {len(segments)} segmentos agrupados em {len(faixas)} faixas candidatas")
    for f in faixas:
        m, s = divmod(int(f["start_sec"]), 60)
        m2, s2 = divmod(int(f["end_sec"]), 60)
        print(f"  [{f['faixa_candidata']:02d}] {m}:{s:02d}-{m2}:{s2:02d}  bpm~{f['bpm_medio']}  \"{f['amostra_letra'][:50]}\"")


if __name__ == "__main__":
    main()
