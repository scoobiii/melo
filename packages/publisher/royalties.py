"""Motor de cálculo de split de royalty entre o ecossistema MELO.

Não define percentuais "corretos" — esses são negociados caso a caso
(autor original via editora/ECAD, artista que regrava, MELO como
plataforma). Este módulo só garante que, dado um plano de split
válido (soma 100%), o cálculo de payout sobre uma receita é correto
e auditável.
"""
from dataclasses import dataclass
from typing import Dict, List

TOLERANCIA_SOMA_PCT = 0.01  # tolerância de arredondamento em pontos percentuais


@dataclass
class RoyaltySplit:
    beneficiario: str  # nome/identificador de quem recebe
    papel: str  # ex.: "autor_original", "artista_regravacao", "melo_plataforma", "editora"
    percentual: float  # 0-100


@dataclass
class RoyaltyPlan:
    faixa: str
    splits: List[RoyaltySplit]

    def __post_init__(self):
        soma = sum(s.percentual for s in self.splits)
        if abs(soma - 100.0) > TOLERANCIA_SOMA_PCT:
            raise ValueError(
                f"Splits de '{self.faixa}' somam {soma}%, não 100%. Corrija os percentuais."
            )
        if any(s.percentual < 0 for s in self.splits):
            raise ValueError("Percentuais de split não podem ser negativos.")


def calculate_payout(plan: RoyaltyPlan, receita_total: float) -> Dict[str, float]:
    """Distribui `receita_total` entre os beneficiários do plano, proporcionalmente."""
    if receita_total < 0:
        raise ValueError("Receita total não pode ser negativa.")

    payout = {}
    for split in plan.splits:
        valor = round(receita_total * (split.percentual / 100.0), 2)
        payout[split.beneficiario] = payout.get(split.beneficiario, 0.0) + valor
    return payout


def revenue_from_streams(streams: int, valor_por_stream: float) -> float:
    """Calcula receita bruta a partir de contagem de streams e valor unitário
    (o valor por stream varia por plataforma e deve ser informado pelo usuário —
    este módulo não assume nenhuma tarifa de mercado)."""
    if streams < 0 or valor_por_stream < 0:
        raise ValueError("Streams e valor por stream não podem ser negativos.")
    return round(streams * valor_por_stream, 2)
