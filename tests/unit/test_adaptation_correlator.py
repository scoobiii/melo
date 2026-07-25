import pytest

from packages.adaptation.correlator import correlate_by_bpm, correlate_genre


def test_correlate_genre_ranks_explicit_related_first():
    resultados = correlate_genre("tipico_panameno")
    nomes = [g.name for g, _ in resultados]
    # forro_pe_de_serra está em `related` explícito de tipico_panameno
    assert nomes[0] == "forro_pe_de_serra"


def test_correlate_genre_scores_are_bounded():
    resultados = correlate_genre("cumbia_panamena", bpm=90)
    for _, score in resultados:
        assert 0.0 <= score <= 1.0


def test_correlate_genre_raises_on_unknown_source():
    with pytest.raises(KeyError):
        correlate_genre("nao_existe")


def test_correlate_by_bpm_prefers_matching_range():
    resultados = correlate_by_bpm(bpm=85, region="brasil")
    top_name = resultados[0][0].name
    # 85 bpm cai dentro do range de pisadinha (80-95) e arrocha (80-100)
    assert top_name in ("pisadinha", "arrocha_sertanejo")
