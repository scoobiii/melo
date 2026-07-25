import pytest

from packages.catalog.store import CatalogStore
from packages.score import calculate_adherence_score, calculate_quality_for_faixa


def test_calculate_adherence_score_high_when_strong_signals():
    resultado = calculate_adherence_score(
        correlacao_score=0.95, confianca_vocal=0.9, tem_transcricao=True
    )
    assert resultado.nivel == "alta"
    assert resultado.valor >= 75


def test_calculate_adherence_score_low_when_weak_correlation_and_no_data():
    resultado = calculate_adherence_score(correlacao_score=0.1)
    assert resultado.nivel == "baixa"
    assert resultado.valor < 50


def test_calculate_adherence_score_warns_when_no_vocal_confidence():
    resultado = calculate_adherence_score(correlacao_score=0.8)
    assert any("Nenhuma voz detectada" in a for a in resultado.avisos)


def test_calculate_adherence_score_warns_when_no_transcricao():
    resultado = calculate_adherence_score(correlacao_score=0.8, confianca_vocal=0.7)
    assert any("Sem transcrição" in a for a in resultado.avisos)


def test_calculate_adherence_score_rejects_out_of_range_correlacao():
    with pytest.raises(ValueError):
        calculate_adherence_score(correlacao_score=1.5)


def test_calculate_adherence_score_rejects_out_of_range_confianca_vocal():
    with pytest.raises(ValueError):
        calculate_adherence_score(correlacao_score=0.5, confianca_vocal=-0.1)


def test_calculate_adherence_score_componentes_sum_matches_valor():
    resultado = calculate_adherence_score(
        correlacao_score=0.7, confianca_vocal=0.6, tem_transcricao=True
    )
    esperado = round(
        resultado.componentes["correlacao_genero"] * 0.60
        + resultado.componentes["confianca_vocal"] * 0.25
        + resultado.componentes["cobertura_dados"] * 0.15,
        1,
    )
    assert resultado.valor == esperado


def test_calculate_quality_for_faixa_uses_catalog_and_adaptation():
    catalog = CatalogStore(":memory:")
    catalog.add_faixa(
        id="faixa-score-1",
        caminho_audio="/tmp/a.wav",
        genero_origem="tipico_panameno",
        bpm=104.0,
    )
    catalog.add_voz_detectada(faixa_id="faixa-score-1", confianca=0.85)
    catalog.add_voz_detectada(faixa_id="faixa-score-1", confianca=0.75)

    scores = calculate_quality_for_faixa(catalog, "faixa-score-1")

    assert len(scores) > 0
    for score in scores.values():
        assert score.componentes["confianca_vocal"] == pytest.approx(80.0, abs=0.1)


def test_calculate_quality_for_faixa_raises_on_unknown_faixa():
    catalog = CatalogStore(":memory:")
    with pytest.raises(ValueError):
        calculate_quality_for_faixa(catalog, "nao-existe")
