# Localização no repo: packages/lyrics/hallucination_filter.py
"""
Detecta padrões conhecidos de alucinação do Whisper — texto que o modelo
"ouve" em trechos de silêncio/instrumental puro, por viés de treino em
dados do YouTube (o clássico "se inscreva no canal" aparecendo do nada).

Achado real desta sessão: segmento 1 de um mix de 175 segmentos saiu
"¡Suscríbete! ¡Suscríbete!" num trecho que era só instrumental. Isso não é
erro aleatório — é um artefato documentado e recorrente do Whisper.

Uso pretendido: rodar sobre a saída de transcribe_audio() ANTES de
alimentar packages/ai/adapter.py — não faz sentido gastar tokens de LLM
tentando "adaptar" texto que não é letra real.
"""

from __future__ import annotations

import re

# Padrões case-insensitive, en/es/pt (Whisper alucina no idioma detectado
# ou mistura com inglês, mesmo pedindo idioma='es' explicitamente)
_PADROES_ALUCINACAO = [
    r"suscr[ií]bete",
    r"subscribe",
    r"like\s+y\s+suscr[ií]bete",
    r"dale\s+like",
    r"activa\s+la\s+campanita",
    r"deja\s+tu\s+like",
    r"comenta\s+abajo",
]

_REGEX_ALUCINACAO = re.compile("|".join(_PADROES_ALUCINACAO), re.IGNORECASE)

# Marcadores que o próprio Whisper usa pra indicar trecho não-vocal —
# não são alucinação, são o modelo relatando corretamente "não há fala
# aqui". Tratados à parte porque não devem virar warning, só reclassificação.
_MARCADORES_INSTRUMENTAL = {"[música]", "[music]", "♪", "[inaudível]", "[inaudible]"}


def parece_alucinacao(texto: str | None) -> bool:
    """True se o texto bate com um padrão conhecido de alucinação do Whisper."""
    if not texto:
        return False
    return bool(_REGEX_ALUCINACAO.search(texto))


def parece_instrumental(texto: str | None) -> bool:
    """True se o texto é só marcador(es) de trecho instrumental (comportamento
    correto do Whisper, não alucinação) — inclusive repetidos, ex:
    '[MÚSICA] [MÚSICA] [MÚSICA]' (padrão real observado em produção)."""
    if not texto:
        return True
    normalizado = texto.strip().lower()
    restante = normalizado
    for marcador in _MARCADORES_INSTRUMENTAL:
        restante = restante.replace(marcador, "")
    # Se depois de remover todos os marcadores conhecidos só sobra espaço
    # em branco, o texto inteiro era composto de marcadores (únicos ou
    # repetidos) -- é instrumental, não alucinação nem letra real.
    return restante.strip() == ""


def classificar_segmento(texto: str | None) -> str:
    """Classifica uma transcrição em: 'vazio', 'instrumental', 'alucinacao',
    ou 'letra_valida'. Uso: filtrar antes de alimentar o adapter de IA."""
    if not texto or not texto.strip():
        return "vazio"
    if parece_alucinacao(texto):
        return "alucinacao"
    if parece_instrumental(texto):
        return "instrumental"
    return "letra_valida"


def filtrar_segmentos(segmentos: list[dict], campo: str = "transcricao") -> dict:
    """Classifica uma lista de segmentos (dicts com campo de transcrição) e
    retorna um resumo + os segmentos marcados com 'classificacao' novo.

    Não remove nada da lista original — só anota, pra decisão humana ou de
    pipeline posterior (ex: só segmentos 'letra_valida' vão pro adapter).
    """
    resumo = {"vazio": 0, "instrumental": 0, "alucinacao": 0, "letra_valida": 0}
    anotados = []
    for seg in segmentos:
        classificacao = classificar_segmento(seg.get(campo))
        resumo[classificacao] += 1
        novo_seg = dict(seg)
        novo_seg["classificacao_transcricao"] = classificacao
        anotados.append(novo_seg)
    return {"segmentos": anotados, "resumo": resumo}
