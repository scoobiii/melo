# Localização no repo: packages/lyrics/transcription_accuracy.py
"""
Mede acurácia de transcrição contra gabarito humano -- não existe
"acurácia" sem alguém ouvir e digitar o correto pra comparar. Este módulo
não inventa número sem gabarito.

Métrica: WER (Word Error Rate), padrão da área de ASR (reconhecimento de
fala) -- não é % de acerto ingênuo, é distância de edição em nível de
palavra (substituições + inserções + remoções) / total de palavras do
gabarito. WER=0.0 é perfeito, WER=1.0 é "errou tudo", pode passar de 1.0
se o modelo alucinar palavras extras.
"""
from __future__ import annotations

import random
import re
from dataclasses import dataclass


def _normalizar(texto: str) -> list[str]:
    """Minúsculo, sem pontuação, tokenizado por espaço -- WER compara
    palavras, não caracteres, e não deve penalizar diferença de
    maiúscula/pontuação que não muda o conteúdo."""
    texto = texto.lower()
    texto = re.sub(r"[^\w\sáéíóúñàâêôãõç]", "", texto)
    return texto.split()


def word_error_rate(referencia: str, hipotese: str) -> float:
    """Calcula WER via distância de Levenshtein em nível de palavra.

    referencia = gabarito humano (o que foi realmente dito/cantado)
    hipotese = saída do Whisper

    Raises:
        ValueError: se referencia for vazia (WER indefinido sem gabarito).
    """
    ref = _normalizar(referencia)
    hip = _normalizar(hipotese)

    if not ref:
        raise ValueError("referencia não pode ser vazia -- WER indefinido")
    if not hip:
        return 1.0  # hipótese vazia = errou 100% do gabarito

    n, m = len(ref), len(hip)
    d = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        d[i][0] = i
    for j in range(m + 1):
        d[0][j] = j
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            custo = 0 if ref[i - 1] == hip[j - 1] else 1
            d[i][j] = min(
                d[i - 1][j] + 1,      # remoção
                d[i][j - 1] + 1,      # inserção
                d[i - 1][j - 1] + custo,  # substituição
            )
    return d[n][m] / n


@dataclass(frozen=True)
class AmostraParaVerificacao:
    indice: int
    start_sec: float
    end_sec: float
    transcricao_whisper: str


def amostrar_segmentos_para_verificacao(
    segmentos: list[dict],
    n: int = 10,
    campo: str = "transcricao",
    seed: int | None = 42,
) -> list[AmostraParaVerificacao]:
    """Sorteia N segmentos com transcrição não-vazia pra verificação manual.

    seed fixo por padrão (42) -- resultado reprodutível entre execuções,
    importante pra comparar WER antes/depois de mudar modelo sem o
    conjunto de amostra mudar junto (variável de confusão).
    """
    candidatos = [s for s in segmentos if s.get(campo)]
    if not candidatos:
        return []
    rng = random.Random(seed)
    escolhidos = rng.sample(candidatos, k=min(n, len(candidatos)))
    return [
        AmostraParaVerificacao(
            indice=s.get("indice", -1),
            start_sec=s.get("start_sec", 0.0),
            end_sec=s.get("end_sec", 0.0),
            transcricao_whisper=s.get(campo, ""),
        )
        for s in escolhidos
    ]


def calcular_wer_medio(pares: list[tuple[str, str]]) -> dict:
    """pares = [(referencia_humana, hipotese_whisper), ...]

    Retorna WER médio + por-segmento, pra distinguir "geralmente bom com
    alguns outliers ruins" de "uniformemente mediano" -- média sozinha
    esconde essa diferença.
    """
    if not pares:
        raise ValueError("Nenhum par fornecido -- não há o que calcular")
    wers = [word_error_rate(ref, hip) for ref, hip in pares]
    return {
        "wer_medio": round(sum(wers) / len(wers), 3),
        "wer_min": round(min(wers), 3),
        "wer_max": round(max(wers), 3),
        "n_amostras": len(wers),
        "wer_por_segmento": [round(w, 3) for w in wers],
    }
