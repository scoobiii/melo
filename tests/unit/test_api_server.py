"""
Testes de apps/api/server.py — servidor HTTP real (ThreadingHTTPServer),
requisições via http.client stdlib (sem requests, consistente com a
filosofia stdlib-only do projeto).

IMPORTANTE: apps/api/server.py cria `store = CatalogStore()` no nível do
módulo, sem db_path explícito — sem isolamento, testes escreveriam no
banco de produção. Todo teste aqui faz monkeypatch de `server.store` para
uma instância :memory: antes de subir o servidor.
"""

import http.client
import json
import threading
from http.server import ThreadingHTTPServer

import pytest

from apps.api import server as server_module
from packages.catalog.store import CatalogStore


@pytest.fixture
def servidor_isolado(monkeypatch):
    """Sobe o servidor real numa porta aleatória, com store :memory:."""
    store_teste = CatalogStore(db_path=":memory:")
    monkeypatch.setattr(server_module, "store", store_teste)

    httpd = ThreadingHTTPServer(("127.0.0.1", 0), server_module.MeloAPIHandler)
    porta = httpd.server_address[1]
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()

    yield porta, store_teste

    httpd.shutdown()
    httpd.server_close()


def _get(porta, path):
    conn = http.client.HTTPConnection("127.0.0.1", porta, timeout=5)
    conn.request("GET", path)
    resp = conn.getresponse()
    corpo = resp.read().decode("utf-8")
    conn.close()
    return resp.status, corpo


def _post(porta, path, corpo_dict=None, corpo_bruto=None):
    conn = http.client.HTTPConnection("127.0.0.1", porta, timeout=5)
    if corpo_bruto is not None:
        payload = corpo_bruto.encode("utf-8")
    else:
        payload = json.dumps(corpo_dict or {}).encode("utf-8")
    conn.request(
        "POST", path, body=payload,
        headers={"Content-Type": "application/json", "Content-Length": str(len(payload))},
    )
    resp = conn.getresponse()
    resposta = resp.read().decode("utf-8")
    conn.close()
    return resp.status, resposta


# ---------- roteamento básico ----------

def test_server_get_health_route(servidor_isolado):
    porta, _store = servidor_isolado
    status, corpo = _get(porta, "/health")

    assert status == 200
    assert json.loads(corpo) == {"status": "ok"}


def test_server_get_rota_inexistente_retorna_404(servidor_isolado):
    porta, _store = servidor_isolado
    status, corpo = _get(porta, "/rota-que-nao-existe")

    assert status == 404
    assert "erro" in json.loads(corpo)


def test_server_post_rota_inexistente_retorna_404(servidor_isolado):
    porta, _store = servidor_isolado
    status, corpo = _post(porta, "/rota-que-nao-existe", corpo_dict={})

    assert status == 404
    assert "erro" in json.loads(corpo)


# ---------- corpo vazio: cai no handler normal com dict vazio ----------

def test_server_post_mixes_sem_corpo_retorna_400_do_handler(servidor_isolado):
    """Corpo vazio -> dados={} -> handlers.criar_mix recusa por campo
    obrigatório faltando. Não é um caso especial do server.py, é o
    handler funcionando como já testamos em test_api_handlers.py — este
    teste só confirma que a integração HTTP -> handler preserva isso."""
    porta, _store = servidor_isolado
    status, corpo = _post(porta, "/mixes", corpo_dict={})

    assert status == 400
    assert "erro" in json.loads(corpo)


# ---------- ACHADO: JSON malformado não é tratado graciosamente ----------

def test_server_post_json_malformado_nao_retorna_erro_estruturado(servidor_isolado):
    """DOCUMENTA UM BUG, não testa comportamento desejado.

    _ler_corpo_json() não tem try/except em torno de json.loads(). Corpo
    malformado levanta JSONDecodeError não capturado dentro do handler
    HTTP — o servidor não devolve um 400 estruturado, a requisição falha
    de forma não-graciosa. Este teste confirma que NÃO recebemos um 400
    limpo hoje; ele deve ser atualizado (e o server.py corrigido com
    try/except ao redor de _ler_corpo_json) quando o bug for corrigido.
    """
    porta, _store = servidor_isolado

    with pytest.raises((http.client.RemoteDisconnected, ConnectionResetError, http.client.BadStatusLine)):
        _post(porta, "/mixes", corpo_bruto="{isso nao e json valido")


# ---------- roteamento extrai ID da URL corretamente ----------

def test_server_roteamento_extrai_mix_track_id_da_url_escrow(servidor_isolado):
    """Confirma que a regex de rota extrai IDs diferentes corretamente,
    não confundindo /mix-tracks/777/escrow com /mix-tracks/1/escrow.
    calculate_payout() não ecoa o nome da faixa na resposta (retorna só
    {beneficiario: valor}), então a prova real é: valores calculados
    batem com receita_total distintas passadas por chamada."""
    porta, _store = servidor_isolado

    status_a, corpo_a = _post(porta, "/mix-tracks/777/escrow", corpo_dict={"receita_total": 50.0})
    status_b, corpo_b = _post(porta, "/mix-tracks/1/escrow", corpo_dict={"receita_total": 999.0})

    assert status_a == 200
    assert status_b == 200
    resultado_a = json.loads(corpo_a)
    resultado_b = json.loads(corpo_b)
    assert resultado_a["status"] == "reservado_em_escrow"
    assert resultado_b["status"] == "reservado_em_escrow"
    assert resultado_a["payout"]["escrow_titular_desconhecido"] == 50.0
    assert resultado_b["payout"]["escrow_titular_desconhecido"] == 999.0
