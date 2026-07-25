# Localização no repo: packages/adaptation/segmentation.py
"""
Segmentação determinística de letra transcrita em blocos (verso, refrão,
ponte). Roda ANTES de qualquer LLM — puramente baseada em estrutura de
texto (linhas em branco separam blocos; blocos repetidos = refrão).

Este módulo não usa IA e não deveria: segmentação estrutural de texto é
uma tarefa de regra, não de geração. Mantê-la determinística significa que
o mesmo texto de entrada sempre produz a mesma segmentação — auditável e
sem custo de API.

Limitação conhecida: a heurística de "refrão = bloco repetido" falha se a
transcrição do Whisper tiver pequenas variações entre repetições (erro de
transcrição, não de segmentação). Isso é aceitável como v1 — normalização
de texto mais tolerante fica para uma iteração futura, não bloqueia uso.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LyricSegment:
    indice: int
    tipo: str  # "verso" | "refrao" | "ponte"
    texto: str


def _normalizar_bloco(bloco: str) -> str:
    """Normalização mínima para comparação de repetição: lowercase e
    espaços colapsados. Não altera o texto original armazenado no segmento.
    """
    return " ".join(bloco.lower().split())


def segment_lyrics(texto_bruto: str) -> list[LyricSegment]:
    """Quebra a letra em blocos por linha em branco, e marca blocos que se
    repetem (normalizados) como 'refrao'. O primeiro bloco nunca-repetido
    é tratado como 'verso'; blocos entre repetições de refrão viram
    'ponte' se não forem os mesmos versos.

    Levanta ValueError se o texto for vazio — segmentar nada não é uma
    operação válida, é um erro de input.
    """
    if not texto_bruto.strip():
        raise ValueError("texto_bruto não pode ser vazio")

    blocos_brutos = [b.strip() for b in texto_bruto.strip().split("\n\n") if b.strip()]
    if not blocos_brutos:
        raise ValueError("Nenhum bloco encontrado após normalizar quebras de linha")

    normalizados = [_normalizar_bloco(b) for b in blocos_brutos]
    contagem = {n: normalizados.count(n) for n in normalizados}

    segmentos: list[LyricSegment] = []
    vistos_como_refrao: set[str] = set()

    for indice, (bloco, norm) in enumerate(zip(blocos_brutos, normalizados)):
        if contagem[norm] > 1:
            tipo = "refrao"
            vistos_como_refrao.add(norm)
        elif indice == 0:
            tipo = "verso"
        else:
            tipo = "verso" if norm not in vistos_como_refrao else "refrao"

        segmentos.append(LyricSegment(indice=indice, tipo=tipo, texto=bloco))

    return segmentos
