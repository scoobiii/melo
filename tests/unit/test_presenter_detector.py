"""Localização no repo: tests/unit/test_presenter_detector.py"""
from packages.presenter_detector.detector import (
    classificar_apresentacao,
    find_self_presentations,
)


def test_classificar_apresentacao_detecta_cantor_pt():
    assert classificar_apresentacao("Eu sou o Dorindo, obrigado por ouvir") == "cantor"


def test_classificar_apresentacao_detecta_cantor_es():
    assert classificar_apresentacao("Hola a todos, soy Ricardo") == "cantor"


def test_classificar_apresentacao_detecta_dj():
    assert classificar_apresentacao("vocês estão ouvindo o melhor típico") == "dj"


def test_classificar_apresentacao_ignora_instrumental():
    assert classificar_apresentacao("[MÚSICA] [MÚSICA] [MÚSICA]") is None


def test_classificar_apresentacao_ignora_texto_sem_padrao():
    assert classificar_apresentacao("dança comigo essa noite meu amor") is None


def test_classificar_apresentacao_ignora_none():
    assert classificar_apresentacao(None) is None


def test_find_self_presentations_filtra_e_anota_tipo():
    segmentos = [
        {"indice": 0, "start_sec": 0.0, "end_sec": 20.8, "transcricao": "[MÚSICA] [MÚSICA]"},
        {"indice": 1, "start_sec": 20.8, "end_sec": 41.2, "transcricao": "Eu sou o Dorindo Cárdenas"},
        {"indice": 2, "start_sec": 41.2, "end_sec": 60.0, "transcricao": "vocês estão ouvindo DJ Phantom"},
    ]
    resultado = find_self_presentations(segmentos)
    assert len(resultado) == 2
    assert resultado[0]["tipo_apresentacao"] == "cantor"
    assert resultado[0]["indice"] == 1
    assert resultado[1]["tipo_apresentacao"] == "dj"
    assert resultado[1]["indice"] == 2


def test_find_self_presentations_nao_modifica_lista_original():
    segmentos = [{"indice": 0, "transcricao": "Eu sou o Dorindo"}]
    find_self_presentations(segmentos)
    assert "tipo_apresentacao" not in segmentos[0]
