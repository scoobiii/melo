# Localização no repo: apps/api/handlers.py
"""
Lógica da API do MELO como funções puras (dict in, (status, dict) out).

Decisão de arquitetura (achado real desta sessão): FastAPI precisa de
pydantic-core, que é Rust/maturin -- mesma classe de falha que já matou
torch, anthropic SDK e faster-whisper/av no Termux (aarch64-linux-android
sem toolchain Rust via rustup). Em vez de tentar de novo com outro
framework, a decisão é: API sem NENHUMA dependência que precise compilar
nativo. Só stdlib (http.server, json) -- ver apps/api/server.py.

Separar a lógica em funções puras aqui (sem tocar em HTTPServer) permite
testar tudo com pytest normal, sem subir servidor, sem mockar request/response.
"""
from __future__ import annotations

from typing import Any

from packages.catalog.store import CatalogStore
from packages.publisher.royalties import RoyaltyPlan, RoyaltySplit, calculate_payout


def criar_mix(dados: dict, store: CatalogStore) -> tuple[int, dict]:
    campos_obrigatorios = {"dj_nome", "arquivo_path"}
    faltando = campos_obrigatorios - dados.keys()
    if faltando:
        return 400, {"erro": f"campos obrigatórios faltando: {sorted(faltando)}"}
    mix_id = store.add_mix(
        dados["dj_nome"], dados["arquivo_path"],
        dados.get("duracao_segundos"), dados.get("plataformas_distribuicao"),
    )
    return 201, {"mix_id": mix_id}


def listar_tracks(mix_id: int, apenas_identificadas: bool, store: CatalogStore) -> tuple[int, Any]:
    tracks = store.list_tracks_for_mix(mix_id, apenas_identificadas)
    return 200, [t.__dict__ for t in tracks]


def identificar_track(mix_track_id: int, dados: dict, store: CatalogStore) -> tuple[int, dict]:
    campos_obrigatorios = {"titulo_identificado", "fingerprint_servico", "fingerprint_confianca"}
    faltando = campos_obrigatorios - dados.keys()
    if faltando:
        return 400, {"erro": f"campos obrigatórios faltando: {sorted(faltando)}"}
    try:
        store.identify_mix_track(
            mix_track_id, dados["titulo_identificado"], dados["fingerprint_servico"],
            dados["fingerprint_confianca"], dados.get("source_artist_id"),
        )
    except ValueError as e:
        return 400, {"erro": str(e)}
    return 200, {"status": "ok"}


def criar_perfil_vocal(dados: dict, store: CatalogStore) -> tuple[int, dict]:
    campos_obrigatorios = {"tessitura", "textura", "nivel"}
    faltando = campos_obrigatorios - dados.keys()
    if faltando:
        return 400, {"erro": f"campos obrigatórios faltando: {sorted(faltando)}"}
    vp_id = store.add_vocal_profile(
        dados["tessitura"], dados["textura"], dados["nivel"], dados.get("notas"),
    )
    return 201, {"vocal_profile_id": vp_id}


def buscar_candidatos_vocais(
    tessitura: str, textura: str, nivel: str | None, store: CatalogStore
) -> tuple[int, Any]:
    candidatos = store.find_destination_artists_by_vocal_profile(tessitura, textura, nivel)
    return 200, [c.__dict__ for c in candidatos]


def criar_gemeo_digital(dados: dict, store: CatalogStore) -> tuple[int, dict]:
    campos_obrigatorios = {"artist_type", "artist_id"}
    faltando = campos_obrigatorios - dados.keys()
    if faltando:
        return 400, {"erro": f"campos obrigatórios faltando: {sorted(faltando)}"}
    try:
        twin_id = store.add_digital_twin(
            dados["artist_type"], dados["artist_id"],
            dados.get("status_consentimento", "nao_licenciado"),
            ativo=dados.get("ativo", False),
        )
    except ValueError as e:
        return 400, {"erro": str(e)}
    return 201, {"digital_twin_id": twin_id}


def calcular_royalty(dados: dict) -> tuple[int, dict]:
    campos_obrigatorios = {"faixa", "splits", "receita_total"}
    faltando = campos_obrigatorios - dados.keys()
    if faltando:
        return 400, {"erro": f"campos obrigatórios faltando: {sorted(faltando)}"}
    try:
        plano = RoyaltyPlan(
            faixa=dados["faixa"],
            splits=[
                RoyaltySplit(s["beneficiario"], s["papel"], s["percentual"])
                for s in dados["splits"]
            ],
        )
        payout = calculate_payout(plano, dados["receita_total"])
    except (ValueError, KeyError) as e:
        return 400, {"erro": str(e)}
    return 200, payout


def reservar_escrow(mix_track_id: int, receita_total: float) -> tuple[int, dict]:
    """Reserva 100% do valor para 'escrow_titular_desconhecido' -- não paga
    DJ/MELO/plataforma até identificação real do titular. Mecanismo real
    de 'fundo para artista fantasma' pedido nesta sessão."""
    try:
        plano = RoyaltyPlan(
            faixa=f"mix_track_{mix_track_id}",
            splits=[RoyaltySplit("escrow_titular_desconhecido", "escrow_pendente", 100.0)],
        )
        payout = calculate_payout(plano, receita_total)
    except ValueError as e:
        return 400, {"erro": str(e)}
    return 200, {"status": "reservado_em_escrow", "payout": payout}


def health() -> tuple[int, dict]:
    return 200, {"status": "ok"}
