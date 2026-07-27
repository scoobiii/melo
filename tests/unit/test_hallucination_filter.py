# Localização no repo: tests/unit/test_hallucination_filter.py
import pytest

from packages.lyrics.hallucination_filter import (
    classificar_segmento,
    filtrar_segmentos,
    parece_alucinacao,
    parece_instrumental,
)


def test_parece_alucinacao_detecta_suscribete():
    assert parece_alucinacao("¡Suscríbete! ¡Suscríbete!")
    assert parece_alucinacao("no olvides darle like y suscribete")


def test_parece_alucinacao_falso_em_letra_normal():
    assert not parece_alucinacao("Escúchalo, ámbar sebeño. Melodías para enamorados.")


def test_parece_alucinacao_none_ou_vazio():
    assert not parece_alucinacao(None)
    assert not parece_alucinacao("")


def test_parece_instrumental_marcador_musica():
    assert parece_instrumental("[MÚSICA]")
    assert parece_instrumental("[MÚSICA] [MÚSICA]")


def test_parece_instrumental_none_conta_como_instrumental():
    assert parece_instrumental(None)


def test_classificar_segmento_vazio():
    assert classificar_segmento("") == "vazio"
    assert classificar_segmento(None) == "vazio"


def test_classificar_segmento_instrumental():
    assert classificar_segmento("[MÚSICA]") == "instrumental"


def test_classificar_segmento_alucinacao():
    assert classificar_segmento("¡Suscríbete! ¡Suscríbete!") == "alucinacao"


def test_classificar_segmento_letra_valida():
    texto = "Quiero vivir en un país donde en verdad puedas entenderme"
    assert classificar_segmento(texto) == "letra_valida"


def test_filtrar_segmentos_resumo_e_anotacao():
    segmentos = [
        {"indice": 0, "transcricao": "[MÚSICA]"},
        {"indice": 1, "transcricao": "¡Suscríbete! ¡Suscríbete!"},
        {"indice": 2, "transcricao": "Quiero vivir en un país"},
        {"indice": 3, "transcricao": None},
    ]
    resultado = filtrar_segmentos(segmentos)
    assert resultado["resumo"] == {
        "vazio": 1, "instrumental": 1, "alucinacao": 1, "letra_valida": 1,
    }
    assert resultado["segmentos"][0]["classificacao_transcricao"] == "instrumental"
    assert resultado["segmentos"][1]["classificacao_transcricao"] == "alucinacao"
    # não altera os campos originais, só adiciona
    assert resultado["segmentos"][2]["indice"] == 2
