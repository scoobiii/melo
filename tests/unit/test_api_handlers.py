# Localização no repo: tests/unit/test_api_handlers.py
import pytest

from apps.api import handlers
from packages.catalog.store import CatalogStore


@pytest.fixture
def store():
    return CatalogStore(":memory:")


def test_criar_mix_ok(store):
    status, corpo = handlers.criar_mix(
        {"dj_nome": "DJ Phantom", "arquivo_path": "mix.wav"}, store
    )
    assert status == 201
    assert "mix_id" in corpo


def test_criar_mix_campo_faltando(store):
    status, corpo = handlers.criar_mix({"dj_nome": "DJ Phantom"}, store)
    assert status == 400
    assert "arquivo_path" in corpo["erro"]


def test_listar_tracks_vazio(store):
    _, mix = handlers.criar_mix({"dj_nome": "DJ X", "arquivo_path": "a.wav"}, store)
    status, corpo = handlers.listar_tracks(mix["mix_id"], False, store)
    assert status == 200
    assert corpo == []


def test_identificar_track_confianca_invalida(store):
    _, mix = handlers.criar_mix({"dj_nome": "DJ X", "arquivo_path": "a.wav"}, store)
    track_id = store.add_mix_track(mix["mix_id"], 0, 0.0, 20.0)
    status, corpo = handlers.identificar_track(
        track_id,
        {"titulo_identificado": "X", "fingerprint_servico": "audd", "fingerprint_confianca": 1.5},
        store,
    )
    assert status == 400
    assert "0 e 1" in corpo["erro"]


def test_criar_perfil_vocal_e_buscar_candidato(store):
    status, corpo = handlers.criar_perfil_vocal(
        {"tessitura": "medio", "textura": "rouco", "nivel": "profissional"}, store
    )
    assert status == 201
    vp_id = corpo["vocal_profile_id"]

    did = store.add_destination_artist("Cantor X", "forro_pe_de_serra")
    with store._connect() as conn:
        conn.execute("UPDATE destination_artists SET vocal_profile_id=? WHERE id=?", (vp_id, did))

    status, corpo = handlers.buscar_candidatos_vocais("medio", "rouco", None, store)
    assert status == 200
    assert len(corpo) == 1
    assert corpo[0]["nome"] == "Cantor X"


def test_criar_gemeo_digital_trava_sem_consentimento(store):
    sid = store.add_source_artist("Artista", "tipico_panameno")
    status, corpo = handlers.criar_gemeo_digital(
        {"artist_type": "source", "artist_id": sid, "ativo": True}, store
    )
    assert status == 400
    assert "consentimento" in corpo["erro"]


def test_criar_gemeo_digital_licenciado_ok(store):
    sid = store.add_source_artist("Artista", "tipico_panameno")
    status, corpo = handlers.criar_gemeo_digital(
        {
            "artist_type": "source", "artist_id": sid,
            "status_consentimento": "licenciado", "ativo": True,
        },
        store,
    )
    assert status == 201
    assert "digital_twin_id" in corpo


def test_calcular_royalty_ok():
    status, payout = handlers.calcular_royalty({
        "faixa": "teste",
        "splits": [
            {"beneficiario": "A", "papel": "autor_original", "percentual": 60.0},
            {"beneficiario": "B", "papel": "melo_plataforma", "percentual": 40.0},
        ],
        "receita_total": 100.0,
    })
    assert status == 200
    assert payout == {"A": 60.0, "B": 40.0}


def test_calcular_royalty_splits_invalidos():
    status, corpo = handlers.calcular_royalty({
        "faixa": "teste",
        "splits": [{"beneficiario": "A", "papel": "x", "percentual": 50.0}],
        "receita_total": 100.0,
    })
    assert status == 400
    assert "100" in corpo["erro"]


def test_reservar_escrow():
    status, corpo = handlers.reservar_escrow(mix_track_id=1, receita_total=50.0)
    assert status == 200
    assert corpo["status"] == "reservado_em_escrow"
    assert corpo["payout"] == {"escrow_titular_desconhecido": 50.0}


def test_health():
    status, corpo = handlers.health()
    assert status == 200
    assert corpo == {"status": "ok"}
