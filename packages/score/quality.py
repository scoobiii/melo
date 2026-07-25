"""Métrica de aderência da análise ao gênero-alvo.

IMPORTANTE — escopo honesto: o MELO ainda não gera áudio (packages/voices
não implementado). Portanto este score NÃO mede qualidade de áudio gerado
— mede a CONFIANÇA da análise que temos hoje (correlação de gênero, dados
vocais detectados, cobertura de transcrição). Quando packages/voices
existir, este módulo precisa ganhar um score específico de qualidade de
áudio gerado; até lá, chamar isso de "quality score de adaptação" seria
prometer mais do que o código entrega.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from packages.adaptation import correlate_genre


@dataclass(frozen=True)
class QualityScore:
    valor: float  # 0-100
    nivel: str  # "baixa" | "media" | "alta"
    componentes: dict
    explicacao: str
    avisos: List[str] = field(default_factory=list)


def _nivel_para(valor: float) -> str:
    if valor >= 75:
        return "alta"
    if valor >= 50:
        return "media"
    return "baixa"


def calculate_adherence_score(
    correlacao_score: float,
    confianca_vocal: Optional[float] = None,
    tem_transcricao: bool = False,
) -> QualityScore:
    """Combina três sinais já existentes no pipeline numa métrica única,
    legível por humanos (não apenas pass/fail):

    - correlacao_score (peso 0.6): saída de packages.adaptation.correlate_genre,
      já 0-1.
    - confianca_vocal (peso 0.25): média de VozDetectada.confianca para a
      faixa, se houver vozes catalogadas. None quando não há dado.
    - cobertura_dados (peso 0.15): 100 se há transcrição, 40 se não —
      não é um "erro", só reduz a confiança do score final.

    Args:
        correlacao_score: 0.0-1.0.
        confianca_vocal: 0.0-1.0 ou None se não houver voz analisada.
        tem_transcricao: se a faixa tem letra transcrita.

    Raises:
        ValueError: se correlacao_score ou confianca_vocal estiverem fora de [0, 1].
    """
    if not 0.0 <= correlacao_score <= 1.0:
        raise ValueError(f"correlacao_score deve estar em [0, 1], recebido: {correlacao_score}")
    if confianca_vocal is not None and not 0.0 <= confianca_vocal <= 1.0:
        raise ValueError(f"confianca_vocal deve estar em [0, 1], recebido: {confianca_vocal}")

    avisos: List[str] = []

    componente_correlacao = round(correlacao_score * 100, 1)

    if confianca_vocal is None:
        componente_vocal = 0.0
        avisos.append(
            "Nenhuma voz detectada/analisada para esta faixa ainda "
            "(packages.catalog.VozDetectada vazio) — componente vocal zerado, "
            "não 'neutro'."
        )
    else:
        componente_vocal = round(confianca_vocal * 100, 1)

    componente_cobertura = 100.0 if tem_transcricao else 40.0
    if not tem_transcricao:
        avisos.append(
            "Sem transcrição disponível — cobertura de dados reduzida, "
            "score final é conservador."
        )

    valor = round(
        componente_correlacao * 0.60
        + componente_vocal * 0.25
        + componente_cobertura * 0.15,
        1,
    )

    componentes = {
        "correlacao_genero": componente_correlacao,
        "confianca_vocal": componente_vocal,
        "cobertura_dados": componente_cobertura,
    }

    nivel = _nivel_para(valor)
    explicacao = (
        f"Score {valor}/100 ({nivel}). Correlação de gênero contribuiu "
        f"{componente_correlacao}/100 (peso 60%), confiança vocal "
        f"{componente_vocal}/100 (peso 25%), cobertura de dados "
        f"{componente_cobertura}/100 (peso 15%)."
    )

    return QualityScore(
        valor=valor,
        nivel=nivel,
        componentes=componentes,
        explicacao=explicacao,
        avisos=avisos,
    )


def calculate_quality_for_faixa(catalog, faixa_id: str, limite_generos: int = 3) -> dict:
    """Wiring de conveniência: busca a faixa no catálogo, roda
    correlate_genre, calcula confiança vocal média a partir de
    VozDetectada, e retorna um QualityScore por gênero de destino
    candidato.

    Args:
        catalog: instância de packages.catalog.store.CatalogStore.
        faixa_id: id da faixa já persistida via catalog.add_faixa(...).

    Returns:
        dict {genero_destino: QualityScore}

    Raises:
        ValueError: se a faixa não existir no catálogo.
    """
    faixa = catalog.get_faixa(faixa_id)
    if faixa is None:
        raise ValueError(f"Faixa não encontrada no catálogo: {faixa_id!r}")

    vozes = catalog.list_vozes_for_faixa(faixa_id)
    confiancas = [v.confianca for v in vozes if v.confianca is not None]
    confianca_vocal = round(sum(confiancas) / len(confiancas), 3) if confiancas else None

    tem_transcricao = False  # o catálogo hoje não persiste transcrição; ver nota no ROADMAP

    ranking = correlate_genre(faixa.genero_origem, bpm=faixa.bpm)

    resultado = {}
    for genero_profile, score in ranking[:limite_generos]:
        resultado[genero_profile.name] = calculate_adherence_score(
            correlacao_score=score,
            confianca_vocal=confianca_vocal,
            tem_transcricao=tem_transcricao,
        )
    return resultado
