"""Motor de correlação: dado um gênero de origem (ou um BPM), rankeia
gêneros correlatos na outra região (panamá <-> brasil)."""
from typing import List, Optional, Tuple

from .genres import GENRE_TABLE, GenreProfile, genres_by_region, get_genre

_REGION_PAIR = {"panama": "brasil", "brasil": "panama"}


def _bpm_proximity_score(bpm: float, candidate: GenreProfile) -> float:
    if candidate.bpm_in_range(bpm):
        return 1.0
    dist = min(abs(bpm - candidate.bpm_min), abs(bpm - candidate.bpm_max))
    return max(0.0, 1.0 - dist / 40.0)  # decai a zero a ~40 bpm de distância


def correlate_genre(
    source_name: str,
    bpm: Optional[float] = None,
) -> List[Tuple[GenreProfile, float]]:
    """Rankeia gêneros da região oposta correlatos ao gênero de origem.

    Score combina: (a) presença na lista `related` explícita (peso 0.6),
    (b) mesma família de textura/instrumentação (peso 0.2), e
    (c) proximidade de BPM, se fornecido (peso 0.2).
    """
    source = get_genre(source_name)
    target_region = _REGION_PAIR[source.region]
    candidates = genres_by_region(target_region)

    results = []
    for cand in candidates:
        score = 0.0
        if cand.name in source.related:
            score += 0.6
        if cand.family == source.family:
            score += 0.2
        if bpm is not None:
            score += 0.2 * _bpm_proximity_score(bpm, cand)
        else:
            score += 0.2 * _bpm_proximity_score(source.bpm_center, cand)
        results.append((cand, round(score, 3)))

    results.sort(key=lambda pair: pair[1], reverse=True)
    return results


def correlate_by_bpm(bpm: float, region: str) -> List[Tuple[GenreProfile, float]]:
    """Rankeia gêneros de uma região só pela proximidade de BPM (sem gênero de origem)."""
    candidates = genres_by_region(region)
    results = [(c, round(_bpm_proximity_score(bpm, c), 3)) for c in candidates]
    results.sort(key=lambda pair: pair[1], reverse=True)
    return results
