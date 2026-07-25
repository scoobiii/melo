"""Tabela estática de perfis de gênero musical (panamenho <-> brasileiro).

Uso: correlacionar gêneros de origem panamenha (típico, cumbia, tamborito —
raízes indígenas/afro) com gêneros brasileiros de forte tradição regional,
como base para decisão de regravação/adaptação.
"""
from dataclasses import dataclass, field
from typing import List


@dataclass
class GenreProfile:
    name: str
    region: str  # "panama" | "brasil"
    bpm_min: float
    bpm_max: float
    family: str  # agrupamento por textura/instrumentação dominante
    related: List[str] = field(default_factory=list)  # nomes correlatos explícitos na outra região

    @property
    def bpm_center(self) -> float:
        return (self.bpm_min + self.bpm_max) / 2

    def bpm_in_range(self, bpm: float) -> bool:
        return self.bpm_min <= bpm <= self.bpm_max


GENRE_TABLE: List[GenreProfile] = [
    # --- Panamá ---
    GenreProfile(
        name="tipico_panameno",
        region="panama",
        bpm_min=95, bpm_max=115,
        family="acordeon_dancante",
        related=["forro_pe_de_serra", "vanerao"],
    ),
    GenreProfile(
        name="cumbia_panamena",
        region="panama",
        bpm_min=85, bpm_max=100,
        family="percussivo_dancante",
        related=["pisadinha", "arrocha_sertanejo"],
    ),
    GenreProfile(
        name="tamborito",
        region="panama",
        bpm_min=100, bpm_max=125,
        family="percussivo_afro_indigena",
        related=["vanerao", "forro_pe_de_serra"],
    ),

    # --- Brasil ---
    GenreProfile(
        name="forro_pe_de_serra",
        region="brasil",
        bpm_min=110, bpm_max=130,
        family="acordeon_dancante",
        related=["tipico_panameno", "tamborito"],
    ),
    GenreProfile(
        name="pisadinha",
        region="brasil",
        bpm_min=80, bpm_max=95,
        family="percussivo_dancante",
        related=["cumbia_panamena"],
    ),
    GenreProfile(
        name="vanerao",
        region="brasil",
        bpm_min=100, bpm_max=120,
        family="percussivo_afro_indigena",
        related=["tamborito", "tipico_panameno"],
    ),
    GenreProfile(
        name="sertanejo_raiz",
        region="brasil",
        bpm_min=90, bpm_max=110,
        family="acordeon_dancante",
        related=["tipico_panameno"],
    ),
    GenreProfile(
        name="sertanejo_universitario",
        region="brasil",
        bpm_min=100, bpm_max=130,
        family="pop_dancante",
        related=[],
    ),
    GenreProfile(
        name="sertanejo_romantico",
        region="brasil",
        bpm_min=70, bpm_max=90,
        family="romantico_lento",
        related=[],
    ),
    GenreProfile(
        name="sertanejo_sofrencia",
        region="brasil",
        bpm_min=70, bpm_max=90,
        family="romantico_lento",
        related=[],
    ),
    GenreProfile(
        name="arrocha_sertanejo",
        region="brasil",
        bpm_min=80, bpm_max=100,
        family="percussivo_dancante",
        related=["cumbia_panamena"],
    ),
]

_BY_NAME = {g.name: g for g in GENRE_TABLE}


def get_genre(name: str) -> GenreProfile:
    if name not in _BY_NAME:
        raise KeyError(f"Gênero desconhecido: {name}. Disponíveis: {sorted(_BY_NAME)}")
    return _BY_NAME[name]


def genres_by_region(region: str) -> List[GenreProfile]:
    return [g for g in GENRE_TABLE if g.region == region]
