import pytest

from packages.publisher.royalties import (
    RoyaltyPlan,
    RoyaltySplit,
    calculate_payout,
    revenue_from_streams,
)


def _plano_valido():
    return RoyaltyPlan(
        faixa="Tipico Mix Adaptado",
        splits=[
            RoyaltySplit("Autor Original", "autor_original", 40.0),
            RoyaltySplit("Artista BR", "artista_regravacao", 40.0),
            RoyaltySplit("MELO", "melo_plataforma", 20.0),
        ],
    )


def test_royalty_plan_accepts_valid_split():
    plano = _plano_valido()
    assert len(plano.splits) == 3


def test_royalty_plan_rejects_split_not_summing_100():
    with pytest.raises(ValueError):
        RoyaltyPlan(
            faixa="Faixa Errada",
            splits=[
                RoyaltySplit("A", "autor_original", 50.0),
                RoyaltySplit("B", "melo_plataforma", 30.0),
            ],
        )


def test_royalty_plan_rejects_negative_percentual():
    with pytest.raises(ValueError):
        RoyaltyPlan(
            faixa="Faixa Negativa",
            splits=[
                RoyaltySplit("A", "autor_original", 110.0),
                RoyaltySplit("B", "melo_plataforma", -10.0),
            ],
        )


def test_calculate_payout_distributes_proportionally():
    plano = _plano_valido()
    payout = calculate_payout(plano, receita_total=1000.0)
    assert payout["Autor Original"] == 400.0
    assert payout["Artista BR"] == 400.0
    assert payout["MELO"] == 200.0
    assert sum(payout.values()) == pytest.approx(1000.0)


def test_calculate_payout_rejects_negative_revenue():
    plano = _plano_valido()
    with pytest.raises(ValueError):
        calculate_payout(plano, receita_total=-50.0)


def test_calculate_payout_merges_duplicate_beneficiarios():
    plano = RoyaltyPlan(
        faixa="Faixa Dupla",
        splits=[
            RoyaltySplit("MELO", "melo_plataforma", 20.0),
            RoyaltySplit("MELO", "editora", 10.0),
            RoyaltySplit("Artista", "artista_regravacao", 70.0),
        ],
    )
    payout = calculate_payout(plano, receita_total=100.0)
    assert payout["MELO"] == 30.0
    assert payout["Artista"] == 70.0


def test_revenue_from_streams_calculates_correctly():
    receita = revenue_from_streams(streams=10_000, valor_por_stream=0.005)
    assert receita == 50.0


def test_revenue_from_streams_rejects_negative_inputs():
    with pytest.raises(ValueError):
        revenue_from_streams(streams=-1, valor_por_stream=0.005)
