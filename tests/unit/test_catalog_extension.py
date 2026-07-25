import pytest

from packages.catalog.store import CatalogStore
from packages.catalog.translation import find_candidatos_traducao


@pytest.fixture
def catalog():
    return CatalogStore(":memory:")


def test_add_and_list_produtores(catalog):
    catalog.add_produtor("Estúdio Raiz", genero_atuacao="forro_pe_de_serra", regiao="PE")
    produtores = catalog.list_produtores(genero_atuacao="forro_pe_de_serra")
    assert len(produtores) == 1
    assert produtores[0].nome == "Estúdio Raiz"


def test_add_and_get_faixa_persists_instrumentos_as_list(catalog):
    catalog.add_faixa(
        id="faixa-001",
        caminho_audio="/tmp/faixa.wav",
        genero_origem="tipico_panameno",
        duracao_segundos=210.5,
        bpm=104.0,
        instrumentos=["acordeón", "caja", "guacharaca"],
    )
    faixa = catalog.get_faixa("faixa-001")
    assert faixa is not None
    assert faixa.bpm == 104.0
    assert faixa.instrumentos == ["acordeón", "caja", "guacharaca"]


def test_get_faixa_returns_none_when_missing(catalog):
    assert catalog.get_faixa("nao-existe") is None


def test_add_faixa_is_idempotent_on_conflict(catalog):
    catalog.add_faixa(id="faixa-002", caminho_audio="/a.wav", genero_origem="tipico_panameno")
    catalog.add_faixa(id="faixa-002", caminho_audio="/b.wav", genero_origem="tipico_panameno")
    faixas = catalog.list_faixas(genero_origem="tipico_panameno")
    assert len(faixas) == 1
    assert faixas[0].caminho_audio == "/b.wav"


def test_add_and_list_vozes_detectadas(catalog):
    catalog.add_faixa(id="faixa-003", caminho_audio="/c.wav", genero_origem="tipico_panameno")
    catalog.add_voz_detectada(
        faixa_id="faixa-003", segmento_indice=0, perfil_vocal="tenor",
        genero_vocal="masculino", confianca=0.82,
    )
    vozes = catalog.list_vozes_for_faixa("faixa-003")
    assert len(vozes) == 1
    assert vozes[0].perfil_vocal == "tenor"


def test_find_candidatos_traducao_ranks_by_correlation(catalog):
    catalog.add_faixa(
        id="faixa-004", caminho_audio="/d.wav",
        genero_origem="tipico_panameno", bpm=104.0,
    )
    catalog.add_destination_artist("Zé do Forró", genero_destino="forro_pe_de_serra", regiao="PE")
    catalog.add_destination_artist("Time do Vanerão", genero_destino="vanerao", regiao="RS")

    candidatos = find_candidatos_traducao(catalog, "faixa-004")

    assert len(candidatos) > 0
    assert candidatos[0].score_correlacao >= candidatos[-1].score_correlacao
    generos_encontrados = {c.genero_destino for c in candidatos}
    assert "forro_pe_de_serra" in generos_encontrados


def test_find_candidatos_traducao_raises_on_unknown_faixa(catalog):
    with pytest.raises(ValueError):
        find_candidatos_traducao(catalog, "nao-existe")
