# Localização no repo: apps/api/server.py
"""
Servidor HTTP do MELO via stdlib pura (http.server + json).

Rodar: python3 -m apps.api.server
Sem uvicorn, sem FastAPI, sem pydantic -- ver handlers.py para o porquê.
"""
from __future__ import annotations

import json
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from apps.api import handlers
from packages.catalog.store import CatalogStore

store = CatalogStore()

_ROTAS_COM_ID = re.compile(r"^/mixes/(\d+)/tracks$")
_ROTA_IDENTIFY = re.compile(r"^/mix-tracks/(\d+)/identify$")
_ROTA_ESCROW = re.compile(r"^/mix-tracks/(\d+)/escrow$")


class MeloAPIHandler(BaseHTTPRequestHandler):
    def _responder(self, status: int, corpo) -> None:
        payload = json.dumps(corpo, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _ler_corpo_json(self) -> dict:
        tamanho = int(self.headers.get("Content-Length", 0))
        if tamanho == 0:
            return {}
        return json.loads(self.rfile.read(tamanho).decode("utf-8"))

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)

        if parsed.path == "/health":
            status, corpo = handlers.health()
        elif (m := _ROTAS_COM_ID.match(parsed.path)):
            apenas_identificadas = query.get("apenas_identificadas", ["false"])[0] == "true"
            status, corpo = handlers.listar_tracks(int(m.group(1)), apenas_identificadas, store)
        elif parsed.path == "/vocal-profiles/match":
            status, corpo = handlers.buscar_candidatos_vocais(
                query.get("tessitura", [""])[0],
                query.get("textura", [""])[0],
                query.get("nivel", [None])[0],
                store,
            )
        else:
            status, corpo = 404, {"erro": "rota não encontrada"}
        self._responder(status, corpo)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        dados = self._ler_corpo_json()

        if parsed.path == "/mixes":
            status, corpo = handlers.criar_mix(dados, store)
        elif (m := _ROTA_IDENTIFY.match(parsed.path)):
            status, corpo = handlers.identificar_track(int(m.group(1)), dados, store)
        elif parsed.path == "/vocal-profiles":
            status, corpo = handlers.criar_perfil_vocal(dados, store)
        elif parsed.path == "/digital-twins":
            status, corpo = handlers.criar_gemeo_digital(dados, store)
        elif parsed.path == "/royalties/calculate":
            status, corpo = handlers.calcular_royalty(dados)
        elif (m := _ROTA_ESCROW.match(parsed.path)):
            status, corpo = handlers.reservar_escrow(
                int(m.group(1)), float(dados.get("receita_total", 0))
            )
        else:
            status, corpo = 404, {"erro": "rota não encontrada"}
        self._responder(status, corpo)

    def log_message(self, format, *args):
        pass  # silencia log padrão verboso; ligar se precisar debugar


def run(host: str = "0.0.0.0", port: int = 8000) -> None:
    servidor = ThreadingHTTPServer((host, port), MeloAPIHandler)
    print(f"MELO API rodando em http://{host}:{port} (Ctrl+C para parar)")
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        servidor.shutdown()


if __name__ == "__main__":
    run()
