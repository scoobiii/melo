# Localização no repo: tests/unit/test_catalog_store.py
"""
Testes de packages/catalog/store.py. Usa SQLite em memória (':memory:'),
nenhum arquivo em disco, nenhuma rede.
"""

import pytest

from packages.catalog.store import CatalogStore


@pytest.fixture
def store():
    return CatalogStore(db_path=":memory:")


def test_add_and_list_source_artist(store):
    store.add_source_artist(
        "Dorindo Cárdenas", "tipico_panameno", pais="Panamá",
        faixa_original="Los Tamboritos",
    )
    artistas = store.list_source_artists(genero_origem="tipico_panameno")
    assert len(artistas) == 1
    assert artistas[0].nome == "Dorindo Cárdenas"
    assert artistas[0].status_licenca == "nao_verificado"


def test_add_source_artist_is_idempotent_on_conflict(store):
    id1 = store.add_source_artist("X", "tipico_panameno", faixa_original="Faixa A")
    id2 = store.add_source_artist(
        "X", "tipico_panameno", faixa_original="Faixa A", status_licenca="licenciado"
    )
    assert id1 == id2
    artistas = store.list_source_artists()
    assert len(artistas) == 1
    assert artistas[0].status_licenca == "licenciado"


def test_add_and_list_destination_artist(store):
    store.add_destination_artist("Cantor BR", "forro_pe_de_serra", regiao="Pernambuco")
    artistas = store.list_destination_artists(genero_destino="forro_pe_de_serra")
    assert len(artistas) == 1
    assert artistas[0].disponivel is True


def test_list_destination_artists_filters_unavailable_by_default(store):
    store.add_destination_artist("A", "vanerao", disponivel=True)
    store.add_destination_artist("B", "vanerao", disponivel=False)
    disponiveis = store.list_destination_artists(genero_destino="vanerao")
    assert len(disponiveis) == 1
    assert disponiveis[0].nome == "A"

    todos = store.list_destination_artists(
        genero_destino="vanerao", apenas_disponiveis=False
    )
    assert len(todos) == 2


def test_map_segment_rejects_invalid_tipo_transformacao(store):
    with pytest.raises(ValueError):
        store.map_segment(
            faixa_id="faixa1",
            segmento_indice=0,
            segmento_tipo="verso",
            tipo_transformacao="magica",
        )


def test_map_segment_and_list_for_faixa(store):
    dest_id = store.add_destination_artist("Cantor BR", "forro_pe_de_serra")
    store.map_segment(
        faixa_id="faixa1",
        segmento_indice=0,
        segmento_tipo="verso",
        destination_artist_id=dest_id,
        tipo_transformacao="direta",
    )
    store.map_segment(
        faixa_id="faixa1",
        segmento_indice=1,
        segmento_tipo="refrao",
        destination_artist_id=dest_id,
        tipo_transformacao="criativa",
    )
    mapeamentos = store.list_mappings_for_faixa("faixa1")
    assert len(mapeamentos) == 2
    assert mapeamentos[0].tipo_transformacao == "direta"
    assert mapeamentos[1].tipo_transformacao == "criativa"


def test_map_segment_upserts_on_conflict(store):
    dest_id = store.add_destination_artist("Cantor BR", "forro_pe_de_serra")
    store.map_segment("faixa1", 0, "verso", destination_artist_id=dest_id)
    store.map_segment("faixa1", 0, "refrao", destination_artist_id=dest_id)
    mapeamentos = store.list_mappings_for_faixa("faixa1")
    assert len(mapeamentos) == 1
    assert mapeamentos[0].segmento_tipo == "refrao"
