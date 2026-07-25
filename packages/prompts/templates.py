# Localização no repo: packages/prompts/templates.py
"""
Prompt engineering para adaptação de letra/estilo entre gêneros
(panamá -> brasil e vice-versa).

Princípios seguidos (docs.claude.com/prompt-engineering):
- system prompt separado do conteúdo variável (facilita cache e teste)
- instruções positivas ("faça X") e negativas ("não faça Y") explícitas
- pedido de raciocínio em etapas antes da resposta final
- saída em tags XML nomeadas, para parsing determinístico río abaixo
- poucos exemplos (few-shot) fixos, não dependentes de dado do usuário

Este módulo NÃO faz chamada de rede. Ele só constrói as strings de prompt.
A chamada em si fica em packages/ai/adapter.py, para que os prompts sejam
testáveis sem precisar de API key nem de rede.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GenreCorrelation:
    """Espelha o formato de saída de packages.adaptation.correlator.

    Mantido como dataclass local (em vez de importar direto) para não
    acoplar packages/prompts a packages/adaptation — se o formato de saída
    do correlator mudar, só este mapeamento precisa ser ajustado.
    """

    source_genre: str
    target_genre: str
    bpm_source: float
    bpm_target_estimate: float
    correlation_score: float  # 0.0 a 1.0


SYSTEM_PROMPT = """\
Você é um especialista em música regional brasileira e panamenha, com foco
em como letra e estrutura rítmica se adaptam entre forró/pisadinha/vanerão/\
sertanejo e típico/cumbia/tamborito.

Sua tarefa é sugerir uma adaptação de letra e frasing rítmica de uma faixa \
de um gênero de origem para um gênero de destino, preservando o sentido \
central da letra original.

Regras obrigatórias:
- Preserve o tema e a narrativa central da letra original. Não invente uma \
história nova.
- Adapte expressões idiomáticas do idioma/região de origem para \
equivalentes naturais no idioma/região de destino — não traduza \
literalmente.
- Ajuste a métrica silábica das linhas para caber no BPM e no fraseado \
típico do gênero de destino informado.
- NÃO gere letra completa de artista real nem cite trechos de canção \
protegida por direito autoral — trabalhe apenas sobre o texto fornecido \
pelo usuário como entrada.
- NÃO invente créditos de autoria. Se a autoria original não for \
informada, deixe o campo correspondente em branco na saída.
- Pense passo a passo antes de responder: primeiro identifique o tema \
central, depois a métrica de destino, só então gere a adaptação.

Formato de saída obrigatório (XML), sem texto fora das tags:
<analysis>
  <theme>tema central identificado, 1-2 frases</theme>
  <target_meter>métrica/fraseado do gênero de destino, breve</target_meter>
</analysis>
<adaptation>
  <lyrics>letra adaptada</lyrics>
  <notes>observações relevantes para o produtor, 1-3 frases</notes>
</adaptation>
"""


def build_user_prompt(
    original_lyrics: str,
    correlation: GenreCorrelation,
) -> str:
    """Monta o prompt de usuário a partir da letra original e da correlação
    de gênero já calculada por packages/adaptation.

    Mantido como função pura (sem I/O) para ser testável sem mocks de rede.
    """
    if not original_lyrics.strip():
        raise ValueError("original_lyrics não pode ser vazio")

    return f"""\
<input>
  <source_genre>{correlation.source_genre}</source_genre>
  <target_genre>{correlation.target_genre}</target_genre>
  <bpm_source>{correlation.bpm_source:.1f}</bpm_source>
  <bpm_target_estimate>{correlation.bpm_target_estimate:.1f}</bpm_target_estimate>
  <correlation_score>{correlation.correlation_score:.2f}</correlation_score>
  <original_lyrics>
{original_lyrics.strip()}
  </original_lyrics>
</input>

Gere a adaptação seguindo exatamente o formato definido no system prompt.
"""


# Few-shot fixo — usado apenas em avaliação/teste de qualidade do prompt,
# não enviado em toda chamada (custaria tokens à toa em produção).
EXAMPLE_CORRELATION = GenreCorrelation(
    source_genre="tipico_panameno",
    target_genre="pisadinha",
    bpm_source=96.0,
    bpm_target_estimate=130.0,
    correlation_score=0.72,
)
