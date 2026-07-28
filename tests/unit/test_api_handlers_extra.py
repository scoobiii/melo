"""
Testes adicionais para apps/api/handlers.py — fecha o gap mapeado em
HANDOFF.md (27/07): 11 testes existentes + 16 novos = 27 pra 100%.

Cada bloco abaixo referencia o endpoint e o branch específico que faltava
na tabela do HANDOFF. Alguns testes (marcados com # ASSUNÇÃO) dependem de
assinaturas de packages/catalog/store.py que não vi completas nesta
sessão — confira contra o código real antes de confiar cegamente.
"""

import pytest

from apps.api import handlers
from packages.catalog.store import CatalogStore


@pytest.fixture
def store():
    return CatalogStore(db_path=":memory:")


# ---------- listar_tracks: 2 branches faltando ----------

def test_listar_tracks_com_filtro_apenas_identificadas(store):
    mix_id = store.add_mix("DJ Teste", "arquivo.wav")
    t1 = store.add_mix_track(mix_id, track_indice=0, inicio_segundos=0.0)
    t2 = store.add_mix_track(mix_id, track_indice=1, inicio_segundos=20.0)
    store.identify_mix_track(t1, "Faixa A", "manual", 0.95)
    # t2 permanece não identificado

    status, corpo = handlers.listar_tracks(mix_id, apenas_identificadas=True, store=store)

    assert status == 200
    assert len(corpo) == 1
    assert corpo[0]["titulo_identificado"] == "Faixa A"


def test_listar_tracks_lista_nao_vazia_sem_filtro(store):
    mix_id = store.add_mix("DJ Teste", "arquivo.wav")
    store.add_mix_track(mix_id, track_indice=0, inicio_segundos=0.0)
    store.add_mix_track(mix_id, track_indice=1, inicio_segundos=20.0)

    status, corpo = handlers.listar_tracks(mix_id, apenas_identificadas=False, store=store)

    assert status == 200
    assert len(corpo) == 2


# ---------- identificar_track: caminho de sucesso + campo faltando ----------

def test_identificar_track_sucesso(store):
    mix_id = store.add_mix("DJ Teste", "arquivo.wav")
    track_id = store.add_mix_track(mix_id, track_indice=0, inicio_segundos=0.0)

    status, corpo = handlers.identificar_track(
        track_id,
        {
            "titulo_identificado": "Faixa X",
            "fingerprint_servico": "manual",
            "fingerprint_confianca": 0.9,
        },
        store,
    )

    assert status == 200
    assert corpo == {"status": "ok"}


def test_identificar_track_campo_faltando(store):
    mix_id = store.add_mix("DJ Teste", "arquivo.wav")
    track_id = store.add_mix_track(mix_id, track_indice=0, inicio_segundos=0.0)

    status, corpo = handlers.identificar_track(
        track_id, {"titulo_identificado": "Faixa X"}, store,
    )

    assert status == 400
    assert "erro" in corpo


# ---------- criar_perfil_vocal: campo faltando ----------

def test_criar_perfil_vocal_campo_faltando(store):
    status, corpo = handlers.criar_perfil_vocal({"tessitura": "grave"}, store)

    assert status == 400
    assert "erro" in corpo


# ---------- buscar_candidatos_vocais: sem match + filtro por nivel ----------

def test_buscar_candidatos_vocais_sem_match_retorna_lista_vazia(store):
    status, corpo = handlers.buscar_candidatos_vocais(
        "grave", "rouca", None, store
    )

    assert status == 200
    assert corpo == []


def test_buscar_candidatos_vocais_filtra_por_nivel(store):
    # ASSUNÇÃO: find_destination_artists_by_vocal_profile aceita nivel=None
    # (sem filtro) vs nivel="profissional" (com filtro) sem lançar erro
    # mesmo sem nenhum artista cadastrado. Confirme contra store.py real
    # se este teste falhar por TypeError de assinatura.
    status_sem_filtro, corpo_sem_filtro = handlers.buscar_candidatos_vocais(
        "grave", "rouca", None, store
    )
    status_com_filtro, corpo_com_filtro = handlers.buscar_candidatos_vocais(
        "grave", "rouca", "profissional", store
    )

    assert status_sem_filtro == 200
    assert status_com_filtro == 200
    assert corpo_sem_filtro == []
    assert corpo_com_filtro == []


# ---------- criar_gemeo_digital: artist_type inválido ----------

def test_criar_gemeo_digital_artist_type_invalido(store):
    status, corpo = handlers.criar_gemeo_digital(
        {"artist_type": "invalido", "artist_id": 1}, store,
    )

    assert status == 400
    assert "erro" in corpo


# ---------- calcular_royalty: campo faltando ----------

def test_calcular_royalty_campo_faltando():
    status, corpo = handlers.calcular_royalty({"faixa": "Faixa X"})

    assert status == 400
    assert "erro" in corpo


# ---------- reservar_escrow: receita_total negativa ----------

def test_reservar_escrow_receita_negativa():
    status, corpo = handlers.reservar_escrow(mix_track_id=1, receita_total=-100.0)

    assert status == 400
    assert "erro" in corpo
