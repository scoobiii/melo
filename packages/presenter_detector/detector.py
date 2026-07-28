"""
Busca segmentos onde cantor ou DJ se auto-apresentam, a partir da
transcricao ja existente por segmento (ex: output/*.json gerado por
scripts/full_mix_analysis.py). Fonte A do bench (o que o MELO entendeu).
Fonte B (anotacao humana ouvindo o audio bruto) ainda nao tem lugar de
armazenamento -- ver docs/BACKLOG.md.

Limitacao real: packages/lyrics/transcriber_cpp.py roda com -nt (sem
timestamp interno do whisper.cpp). A granularidade temporal daqui vem
so da fronteira do segmento (start_sec/end_sec, definida por BPM/timbre
em packages/adaptation/mix_segmentation.py), nao do instante exato da
frase dentro do segmento.
"""
from __future__ import annotations

import re
from pathlib import Path

from packages.lyrics.hallucination_filter import parece_instrumental

# Nome próprio = palavra capitalizada, não pronome/artigo comum que apareceria
# depois de "soy"/"eu sou" numa frase de letra de música ("soy tu", "sou o que").
_PALAVRA_NOME_PROPRIO = r"[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+"

# (?i:...) aplica case-insensitive só na frase-gatilho -- a classe de nome
# próprio precisa continuar exigindo maiúscula de verdade, senão volta a
# aceitar "soy tu"/"sou o" como falso positivo (achado real, sessão 28/07).
_PADROES_CANTOR = [
    re.compile(rf"(?i:\bmeu nome[\s\S]{{0,3}}é\s+){_PALAVRA_NOME_PROPRIO}\b"),
    re.compile(rf"(?i:\beu sou[oa]?\s+(?:o\s+|a\s+)?){_PALAVRA_NOME_PROPRIO}\b"),
    re.compile(rf"(?i:\bme llamo\s+){_PALAVRA_NOME_PROPRIO}\b"),
    re.compile(rf"(?i:\bsoy\s+){_PALAVRA_NOME_PROPRIO}\b"),
    re.compile(r"\bquem canta\s+(aqui\s+)?é\b", re.IGNORECASE),
]

_PADROES_DJ = [
    re.compile(r"\baqui[\s\S]{0,3}(é|quem fala é)\s+o?\s*dj\b", re.IGNORECASE),
    re.compile(r"\bdj\s+\w+\s+na\s+mistura\b", re.IGNORECASE),
    re.compile(r"\bvocês estão ouvindo\b", re.IGNORECASE),
    re.compile(r"\ben la mezcla\b", re.IGNORECASE),
    re.compile(r"\btoca(ndo)? pra vocês\b", re.IGNORECASE),
]


def classificar_apresentacao(texto: str | None) -> str | None:
    """Retorna 'cantor', 'dj', ou None. Ignora segmentos que o filtro de
    alucinação já classifica como instrumental/silêncio -- não faz sentido
    procurar autoapresentação em '[MÚSICA]'."""
    if not texto or parece_instrumental(texto):
        return None
    for padrao in _PADROES_CANTOR:
        if padrao.search(texto):
            return "cantor"
    for padrao in _PADROES_DJ:
        if padrao.search(texto):
            return "dj"
    return None


def find_self_presentations(segmentos: list[dict], campo: str = "transcricao") -> list[dict]:
    """Varre uma lista de segmentos (mesmo formato de output/*.json:
    dicts com start_sec, end_sec, indice, <campo>) e retorna só os que
    batem com padrão de autoapresentação, anotados com 'tipo_apresentacao'.
    Não modifica a lista original."""
    encontrados = []
    for seg in segmentos:
        tipo = classificar_apresentacao(seg.get(campo))
        if tipo is not None:
            encontrados.append({**seg, "tipo_apresentacao": tipo})
    return encontrados


def _normalizar_segmentos(dado: dict | list) -> list[dict]:
    """Converte os 3 formatos reais encontrados em output/*.json pro mesmo
    shape (dict achatado com start_sec/end_sec/transcricao) que
    find_self_presentations espera. Não escreve nada em disco, não modifica
    o dado original.

    Formato A: lista de dicts com start_sec/end_sec/transcricao no raiz
               (scripts/full_mix_analysis.py) -- retorna como está.
    Formato B: dict único com transcricao no raiz, sem segmentação
               (packages/pipeline) -- vira lista de 1 item; sem start_sec/
               end_sec reais, usa 0.0 e duration_seconds se existir.
    Formato C: dict com d['segments'], cada item com audio_segment.start_sec/
               end_sec aninhado -- achata pro nível raiz.
    """
    if isinstance(dado, list):
        return dado  # Formato A

    if isinstance(dado, dict) and "segments" in dado:
        achatados = []
        for seg in dado["segments"]:
            audio_seg = seg.get("audio_segment", {})
            achatados.append({
                **seg,
                "start_sec": audio_seg.get("start_sec"),
                "end_sec": audio_seg.get("end_sec"),
                "indice": audio_seg.get("indice"),
            })
        return achatados  # Formato C

    if isinstance(dado, dict) and "transcricao" in dado:
        return [{
            "start_sec": 0.0,
            "end_sec": dado.get("duration_seconds"),
            "indice": 0,
            "transcricao": dado.get("transcricao"),
        }]  # Formato B

    raise ValueError(f"Formato de output não reconhecido: chaves {list(dado.keys()) if isinstance(dado, dict) else type(dado)}")


def find_self_presentations_em_arquivo(caminho: str, campo: str = "transcricao") -> list[dict]:
    """Lê um output/*.json (qualquer um dos 3 formatos reais do projeto) e
    já retorna os matches de autoapresentação, sem o caller precisar saber
    qual formato é."""
    import json

    dado = json.loads(Path(caminho).read_text(encoding="utf-8"))
    segmentos = _normalizar_segmentos(dado)
    return find_self_presentations(segmentos, campo=campo)
