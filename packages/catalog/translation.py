"""Wiring entre o catálogo (packages.catalog) e a correlação de gênero
(packages.adaptation): dado o id de uma faixa já catalogada, responde
"quem já pode tocar/produzir essa adaptação" cruzando os gêneros de
destino correlatos com os artistas de destino cadastrados.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from packages.adaptation import correlate_genre

from .store import CatalogStore, DestinationArtist


@dataclass(frozen=True)
class CandidatoTraducao:
    genero_destino: str
    score_correlacao: float
    artistas: List[DestinationArtist]


def find_candidatos_traducao(
    catalog: CatalogStore,
    faixa_id: str,
    limite_generos: int = 3,
) -> List[CandidatoTraducao]:
    """Para uma faixa já catalogada, rankeia gêneros de destino correlatos
    (via packages.adaptation.correlate_genre) e lista, para cada um, os
    artistas de destino já cadastrados e disponíveis.

    Raises:
        ValueError: se a faixa não existir no catálogo.
    """
    faixa = catalog.get_faixa(faixa_id)
    if faixa is None:
        raise ValueError(f"Faixa não encontrada no catálogo: {faixa_id!r}")

    ranking = correlate_genre(faixa.genero_origem, bpm=faixa.bpm)

    candidatos = []
    for genero_profile, score in ranking[:limite_generos]:
        artistas = catalog.list_destination_artists(genero_destino=genero_profile.name)
        candidatos.append(
            CandidatoTraducao(
                genero_destino=genero_profile.name,
                score_correlacao=score,
                artistas=artistas,
            )
        )
    return candidatos
