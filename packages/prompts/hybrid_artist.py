"""
packages/prompts/hybrid_artist.py

Prompt engineering para o conceito de "artista híbrido" (Fase 2 do ROADMAP:
packages/score + packages/prompts). Módulo isolado, sem I/O — recebe a saída
já calculada por packages/adaptation e packages/score, monta as mensagens
para a chamada LLM (via packages/ai) e faz o parsing da resposta XML.

Restrições de design (deliberadas):
- Nunca referencia artista real, vivo ou morto, como atalho de timbre.
- Recusa a fusão quando score_aderencia < LIMIAR_RECUSA, em vez de forçar
  um conceito — evita que o modelo "resolva" uma correlação fraca inventando
  confiança que os dados não sustentam.
- Saída em XML para reaproveitar o parser que packages/ai já usa (retries +
  parsing XML), em vez de introduzir um segundo formato (JSON) no pipeline.
"""

from dataclasses import dataclass
import re

LIMIAR_RECUSA = 0.5

SYSTEM_PROMPT = """\
Você é um diretor musical especializado em fusão de gêneros regionais
(tradição panamenha e brasileira).

Regras obrigatórias:
1. Descreva sempre um artista FICTÍCIO. Nunca use um artista real, vivo ou
   morto, como referência de timbre, nome ou identidade visual — mesmo como
   comparação ("estilo de X"). Descreva características vocais em termos
   técnicos: tessitura, textura (rouco/limpo/nasal), ornamentação, fraseado,
   vibrato.
2. Se o score_aderencia recebido for menor que 0.5, NÃO crie o conceito de
   artista. Responda apenas com <recusa> explicando, em termos musicais
   objetivos, por que os dois gêneros não sustentam uma fusão coerente.
3. Toda afirmação sobre por que a fusão funciona deve se apoiar nos dados
   fornecidos (correlações, bpm, cobertura_de_dados) — não invente dados
   novos.
4. Responda estritamente no formato XML especificado, sem texto fora das
   tags.
"""

RESPONSE_FORMAT = """\
Formato de resposta (escolha UM dos dois blocos):

<hybrid_artist>
  <nome_artistico>...</nome_artistico>
  <timbre_vocal>...</timbre_vocal>
  <fraseado_tipico>...</fraseado_tipico>
  <instrumentacao_sugerida>item; item; item</instrumentacao_sugerida>
  <conceito_visual>...</conceito_visual>
  <justificativa>...</justificativa>
</hybrid_artist>

OU, se score_aderencia < 0.5:

<recusa>
  <motivo>...</motivo>
</recusa>
"""

FEW_SHOT_EXAMPLES = [
    {
        "input": (
            "gênero_origem: tipico_panameno\n"
            "bpm: 95.7\n"
            "correlações: forro_pe_de_serra: 0.929, vanerao: 0.778\n"
            "score_aderencia: 0.86\n"
            "cobertura_de_dados: alta"
        ),
        "output": (
            "<hybrid_artist>"
            "<nome_artistico>Serra do Istmo</nome_artistico>"
            "<timbre_vocal>médio-grave, textura limpa com leve nasalidade, "
            "vibrato curto no final de frase</timbre_vocal>"
            "<fraseado_tipico>frases curtas com respiro marcado, acentuação "
            "na batida forte do compasso</fraseado_tipico>"
            "<instrumentacao_sugerida>sanfona; caixa; violão de baixaria; "
            "percussão de tamborito</instrumentacao_sugerida>"
            "<conceito_visual>figurino que combina cores térreas do Panamá "
            "interiorano com estampas de bandeira do forró nordestino, sem "
            "referência a traje de artista específico</conceito_visual>"
            "<justificativa>score 0.86 e cobertura alta sustentam a fusão; "
            "BPM 95.7 está dentro da faixa típica de forró pé-de-serra"
            "</justificativa>"
            "</hybrid_artist>"
        ),
    },
    {
        "input": (
            "gênero_origem: cumbia_panamena\n"
            "bpm: 140.2\n"
            "correlações: sertanejo_universitario: 0.31\n"
            "score_aderencia: 0.28\n"
            "cobertura_de_dados: baixa"
        ),
        "output": (
            "<recusa><motivo>score_aderencia 0.28 e cobertura de dados "
            "baixa não sustentam uma fusão coerente; BPM 140.2 é "
            "incompatível com a faixa típica de sertanejo universitário, "
            "indicando correlação espúria</motivo></recusa>"
        ),
    },
]


@dataclass
class AderenciaInput:
    genero_origem: str
    bpm: float
    correlacoes: dict  # {genero: score}
    score_aderencia: float
    cobertura_de_dados: str  # "alta" | "media" | "baixa"


@dataclass
class HybridArtist:
    nome_artistico: str
    timbre_vocal: str
    fraseado_tipico: str
    instrumentacao_sugerida: list
    conceito_visual: str
    justificativa: str


@dataclass
class Recusa:
    motivo: str


def _formatar_correlacoes(correlacoes: dict) -> str:
    return ", ".join(f"{genero}: {score:.2f}" for genero, score in correlacoes.items())


def build_messages(dados: AderenciaInput) -> list:
    """Monta a lista de mensagens (system + few-shot + input real) para a
    chamada via packages/ai. Não faz nenhuma chamada de rede — só monta a
    estrutura de mensagens."""
    few_shot_text = "\n\n".join(
        f"Entrada:\n{ex['input']}\n\nSaída:\n{ex['output']}" for ex in FEW_SHOT_EXAMPLES
    )

    entrada_real = (
        f"gênero_origem: {dados.genero_origem}\n"
        f"bpm: {dados.bpm}\n"
        f"correlações: {_formatar_correlacoes(dados.correlacoes)}\n"
        f"score_aderencia: {dados.score_aderencia}\n"
        f"cobertura_de_dados: {dados.cobertura_de_dados}"
    )

    return [
        {"role": "system", "content": SYSTEM_PROMPT + "\n" + RESPONSE_FORMAT},
        {
            "role": "user",
            "content": (
                f"Exemplos:\n\n{few_shot_text}\n\n"
                f"Agora gere a resposta para esta entrada:\n\n{entrada_real}"
            ),
        },
    ]


def _extrair_tag(xml: str, tag: str) -> str | None:
    match = re.search(fr"<{tag}>(.*?)</{tag}>", xml, re.DOTALL)
    return match.group(1).strip() if match else None


def parse_response(xml: str) -> HybridArtist | Recusa:
    """Faz o parsing da resposta XML do modelo. Levanta ValueError se o
    formato não corresponder a nenhum dos dois blocos esperados — falha
    explícita em vez de retorno parcial/adivinhado."""
    if "<recusa>" in xml:
        motivo = _extrair_tag(xml, "motivo")
        if motivo is None:
            raise ValueError("Bloco <recusa> sem <motivo>.")
        return Recusa(motivo=motivo)

    if "<hybrid_artist>" in xml:
        campos = [
            "nome_artistico",
            "timbre_vocal",
            "fraseado_tipico",
            "instrumentacao_sugerida",
            "conceito_visual",
            "justificativa",
        ]
        valores = {campo: _extrair_tag(xml, campo) for campo in campos}
        faltando = [c for c, v in valores.items() if v is None]
        if faltando:
            raise ValueError(f"Campos ausentes na resposta: {faltando}")

        return HybridArtist(
            nome_artistico=valores["nome_artistico"],
            timbre_vocal=valores["timbre_vocal"],
            fraseado_tipico=valores["fraseado_tipico"],
            instrumentacao_sugerida=[
                item.strip() for item in valores["instrumentacao_sugerida"].split(";")
            ],
            conceito_visual=valores["conceito_visual"],
            justificativa=valores["justificativa"],
        )

    raise ValueError("Resposta não contém <hybrid_artist> nem <recusa>.")
