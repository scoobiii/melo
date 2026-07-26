"""
tests/test_hybrid_artist.py

Testes de packages/prompts/hybrid_artist.py. Não fazem nenhuma chamada de
rede — testam só a lógica pura (montagem de mensagens + parsing), que é
justamente o motivo de o módulo ser "isolado sem I/O".
"""

import pytest

from packages.prompts.hybrid_artist import (
    AderenciaInput,
    HybridArtist,
    Recusa,
    build_messages,
    parse_response,
)


# ---------- fixtures de entrada ----------

@pytest.fixture
def entrada_aderente():
    return AderenciaInput(
        genero_origem="tipico_panameno",
        bpm=95.7,
        correlacoes={"forro_pe_de_serra": 0.929, "vanerao": 0.778},
        score_aderencia=0.86,
        cobertura_de_dados="alta",
    )


@pytest.fixture
def entrada_fraca():
    return AderenciaInput(
        genero_origem="cumbia_panamena",
        bpm=140.2,
        correlacoes={"sertanejo_universitario": 0.31},
        score_aderencia=0.28,
        cobertura_de_dados="baixa",
    )


# ---------- build_messages ----------

def test_build_messages_inclui_system_prompt_com_regras_obrigatorias():
    entrada = AderenciaInput("x", 100.0, {"y": 0.5}, 0.5, "media")
    mensagens = build_messages(entrada)

    system = mensagens[0]["content"]
    assert "NUNCA" in system.upper() or "Nunca" in system
    assert "artista real" in system
    assert "0.5" in system or "0,5" in system  # limiar de recusa documentado


def test_build_messages_inclui_few_shot_e_dados_reais(entrada_aderente):
    mensagens = build_messages(entrada_aderente)
    user_content = mensagens[1]["content"]

    # few-shot presente
    assert "Serra do Istmo" in user_content
    # dados reais da entrada presentes, não só o exemplo
    assert "tipico_panameno" in user_content
    assert "0.86" in user_content


def test_build_messages_nao_faz_chamada_de_rede(entrada_aderente, monkeypatch):
    # se algum import escondido tentasse rede, isso pegaria — mas o ponto
    # principal é documentar a garantia: build_messages é função pura.
    import socket

    def bloqueado(*args, **kwargs):
        raise AssertionError("build_messages não deveria tocar em rede")

    monkeypatch.setattr(socket, "socket", bloqueado)
    build_messages(entrada_aderente)  # não deve levantar


# ---------- parse_response: caso aceito ----------

def test_parse_response_hybrid_artist_completo():
    xml = (
        "<hybrid_artist>"
        "<nome_artistico>Serra do Istmo</nome_artistico>"
        "<timbre_vocal>médio-grave, textura limpa</timbre_vocal>"
        "<fraseado_tipico>frases curtas</fraseado_tipico>"
        "<instrumentacao_sugerida>sanfona; caixa; violão</instrumentacao_sugerida>"
        "<conceito_visual>cores térreas</conceito_visual>"
        "<justificativa>score 0.86 sustenta a fusão</justificativa>"
        "</hybrid_artist>"
    )
    resultado = parse_response(xml)

    assert isinstance(resultado, HybridArtist)
    assert resultado.nome_artistico == "Serra do Istmo"
    assert resultado.instrumentacao_sugerida == ["sanfona", "caixa", "violão"]


# ---------- parse_response: recusa ----------

def test_parse_response_recusa():
    xml = "<recusa><motivo>score baixo, correlação espúria</motivo></recusa>"
    resultado = parse_response(xml)

    assert isinstance(resultado, Recusa)
    assert "score baixo" in resultado.motivo


# ---------- parse_response: malformado ----------

def test_parse_response_sem_tag_reconhecida_levanta_erro():
    with pytest.raises(ValueError, match="não contém"):
        parse_response("<resposta>algo inesperado</resposta>")


def test_parse_response_hybrid_artist_com_campo_faltando_levanta_erro():
    xml_incompleto = (
        "<hybrid_artist>"
        "<nome_artistico>Serra do Istmo</nome_artistico>"
        "</hybrid_artist>"
    )
    with pytest.raises(ValueError, match="ausentes"):
        parse_response(xml_incompleto)


def test_parse_response_recusa_sem_motivo_levanta_erro():
    with pytest.raises(ValueError, match="sem <motivo>"):
        parse_response("<recusa></recusa>")


# ---------- teste de integração ponta a ponta (sem rede) ----------

def test_fluxo_completo_score_baixo_deveria_gerar_prompt_pedindo_recusa(entrada_fraca):
    mensagens = build_messages(entrada_fraca)
    # o prompt deve carregar o score real (0.28) para o modelo decidir recusar
    assert "0.28" in mensagens[1]["content"]

    # simulando o que o modelo, seguindo o system prompt, deveria responder
    resposta_simulada = "<recusa><motivo>score 0.28 abaixo do limiar</motivo></recusa>"
    resultado = parse_response(resposta_simulada)
    assert isinstance(resultado, Recusa)
