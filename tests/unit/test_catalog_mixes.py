# Localização no repo: tests/unit/test_catalog_mixes.py
"""
Testes de packages/catalog/store.py para mixes/mix_tracks — o caso real
de um arquivo de DJ contendo múltiplas faixas de artistas diferentes.
"""

import pytest

from packages.catalog.store import CatalogStore


@pytest.fixture
def store():
    return CatalogStore(db_path=":memory:")


def test_add_mix_and_retrieve_by_path(store):
    mix_id = store.add_mix(
        dj_nome="DJ Phantom",
        arquivo_path="assets/samples/dj_phantom.wav",
        duracao_segundos=3724.83,
        plataformas_distribuicao=["youtube", "soundcloud"],
    )
    mix = store.get_mix_by_path("assets/samples/dj_phantom.wav")
    assert mix.id == mix_id
    assert mix.dj_nome == "DJ Phantom"
    assert "youtube" in mix.plataformas_distribuicao


def test_add_mix_is_idempotent_on_path_conflict(store):
    id1 = store.add_mix("DJ A", "arquivo.wav", duracao_segundos=100.0)
    id2 = store.add_mix("DJ A (nome corrigido)", "arquivo.wav", duracao_segundos=100.0)
    assert id1 == id2


def test_add_and_list_mix_tracks(store):
    mix_id = store.add_mix("DJ Phantom", "mix.wav")
    store.add_mix_track(mix_id, track_indice=0, inicio_segundos=0.0, fim_segundos=200.0)
    store.add_mix_track(mix_id, track_indice=1, inicio_segundos=200.0, fim_segundos=400.0)

    tracks = store.list_tracks_for_mix(mix_id)
    assert len(tracks) == 2
    assert tracks[0].status_identificacao == "nao_identificado"


def test_identify_mix_track_high_confidence_marks_identificado(store):
    mix_id = store.add_mix("DJ Phantom", "mix.wav")
    track_id = store.add_mix_track(mix_id, track_indice=0, inicio_segundos=0.0)
    sid = store.add_source_artist("Artista X", "tipico_panameno")

    store.identify_mix_track(
        track_id, "Faixa Y", "acrcloud", 0.9, source_artist_id=sid
    )
    tracks = store.list_tracks_for_mix(mix_id)
    assert tracks[0].status_identificacao == "identificado"
    assert tracks[0].source_artist_id == sid


def test_identify_mix_track_low_confidence_marks_incerta(store):
    mix_id = store.add_mix("DJ Phantom", "mix.wav")
    track_id = store.add_mix_track(mix_id, track_indice=0, inicio_segundos=0.0)

    store.identify_mix_track(track_id, "Faixa Y", "acrcloud", 0.3)
    tracks = store.list_tracks_for_mix(mix_id)
    assert tracks[0].status_identificacao == "identificacao_incerta"


def test_identify_mix_track_rejects_confidence_out_of_range(store):
    mix_id = store.add_mix("DJ Phantom", "mix.wav")
    track_id = store.add_mix_track(mix_id, track_indice=0, inicio_segundos=0.0)

    with pytest.raises(ValueError):
        store.identify_mix_track(track_id, "Faixa Y", "acrcloud", 1.5)


def test_list_tracks_for_mix_filters_only_identified(store):
    mix_id = store.add_mix("DJ Phantom", "mix.wav")
    t1 = store.add_mix_track(mix_id, track_indice=0, inicio_segundos=0.0)
    t2 = store.add_mix_track(mix_id, track_indice=1, inicio_segundos=200.0)
    t3 = store.add_mix_track(mix_id, track_indice=2, inicio_segundos=400.0)

    store.identify_mix_track(t1, "Faixa A", "acrcloud", 0.95)
    store.identify_mix_track(t2, "Faixa B", "acrcloud", 0.4)  # incerta
    # t3 nunca identificada

    apenas_prontas = store.list_tracks_for_mix(mix_id, apenas_identificadas=True)
    assert len(apenas_prontas) == 1
    assert apenas_prontas[0].titulo_identificado == "Faixa A"
