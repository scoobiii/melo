import pytest

from packages.adaptation.genres import get_genre, genres_by_region


def test_get_genre_returns_known_profile():
    g = get_genre("tipico_panameno")
    assert g.region == "panama"
    assert g.bpm_min < g.bpm_max


def test_get_genre_raises_on_unknown():
    with pytest.raises(KeyError):
        get_genre("genero_inexistente")


def test_genres_by_region_filters_correctly():
    panama = genres_by_region("panama")
    brasil = genres_by_region("brasil")
    assert all(g.region == "panama" for g in panama)
    assert all(g.region == "brasil" for g in brasil)
    assert len(panama) == 3
    assert len(brasil) == 8
