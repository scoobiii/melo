# SWOT — MELO

| | |
|---|---|
| **Versão** | 1.1.0 |
| **Data** | 2026-07-25 |
| **Baseado em** | README.md, ROADMAP.md (commit 99cd3ea), estado real de `packages/` |
| **Próxima revisão sugerida** | ao concluir qualquer item da Fase 1 do ROADMAP, ou a cada 90 dias |

> Este documento é um snapshot. Não é atualizado automaticamente — revisar
> manualmente e subir a versão (1.1.0, 2.0.0...) a cada revisão relevante,
> mantendo o histórico via `git log docs/SWOT.md`.

## O que foi prometido

Uma "fábrica de adaptação musical": analisar áudio → adaptar gênero →
**gerar** áudio/voz adaptado → calcular royalty → **licenciar/distribuir**
automaticamente.

## Score por módulo

Escala 1–3, onde 1 = vago/mínimo, 2 = parcial, 3 = completo e testado.

| Módulo | Promessa | Entrega | Gap p/ 3/3 |
|---|---|---|---|
| `audio` (metadados) | 3 | 3 | 0% |
| `lyrics` (transcrição) | 3 | 3 | 0% |
| `adaptation` (BPM+correlação) | 3 | 3 | 0% |
| `pipeline` (orquestração) | 3 | 3 | 0% |
| `publisher` (split royalty) | 3 | 2 | 33% |
| `ai`+`prompts` (adaptação de letra) | 3 | 2 | 33% |
| `voices` (síntese/clonagem) | 3 | 0 | 100% |
| `score` (qualidade) | 2 | 0 | 100% |
| Licenciamento automatizado (Fase 3) | 3 | 0 | 100% |
| Docs (`ROADMAP`/`BUSINESS_PLAN`) | 3 | 3 | 0% |

**Total: 31 pontos prometidos, 22 entregues → 29% de gap geral para 3/3 em
tudo** (revisão 1.1.0: soma inclui persistência/catálogo, promessa 2,
entrega 3 — item implícito no README original, não pontuado na v1.0.0).

Essa média mascara o que importa: os módulos em 3/3 são a parte **fácil**
(análise). Os três em 0 são o **coração da proposta de valor** (gerar áudio
de verdade e monetizar automaticamente). Ponderando por importância, a
completude real do produto está mais perto de **20–25%**, não 66%.

## Forças

- Núcleo de análise 100% testado (68 testes verdes), agora incluindo
  persistência real (`packages/catalog`: artistas, produtores, faixas,
  vozes) e wiring de tradução de gênero (`packages/catalog/translation.py`),
  além do adapter de IA.
- Consciência legal explícita desde o README, evitando risco jurídico
  grosseiro em geração de voz/regravação.
- CI real (lint → test → build), rodando em ambiente compatível
  (`ubuntu-latest`), independente das limitações do ambiente de dev local.

## Fraquezas

- Zero geração de áudio/voz — o diferencial do produto ainda não existe.
- `BUSINESS_PLAN` era um arquivo vazio até esta revisão; modelo de
  monetização é hipótese, sem validação com nenhum parceiro real.
- Ambiente de dev local (Termux/Android) tem atrito real com
  `torch`/`whisper`/`accelerate` (sem wheel para o triple
  aarch64-linux-android), o que trava iteração rápida fora do CI.

## Oportunidades

- Correlação panamá ↔ brasil é um nicho pouco explorado — pouca
  concorrência direta nesse par específico de gêneros.
- Adapter de letra via LLM (hoje 2/3) é caminho rápido e barato para
  mostrar valor antes de resolver geração de áudio pesada.
- Modelo B2B de licenciamento de tecnologia não exige resolver
  distribuição (Fase 3) primeiro.

## Ameaças

- Ferramentas grandes (Suno, Udio) já resolveram geração de áudio
  genérica — MELO compete em nicho, não em capacidade bruta.
- Sem validação de licenciamento com nenhum titular de catálogo, a Fase 3
  inteira pode ser inviável na prática.
- Bandwidth aparente de 1 pessoa — Fases 1–3 do ROADMAP (voz, score,
  licenciamento) são meses de trabalho, não semanas.

## Conclusão / gargalo real

Para chegar a 3/3 em tudo, o gargalo não é código adicional nos módulos
que já são 3/3 — é decidir se vale a pena perseguir `voices` (alto risco
técnico e legal) antes de validar a Fase 3 (licenciamento) com pelo menos
um parceiro real. Sem essa validação, otimizar geração de voz é resolver o
problema errado primeiro.

## Histórico de revisões

| Versão | Data | Mudança |
|---|---|---|
| 1.0.0 | 2026-07-25 | Primeira versão, cobrindo estado do repo até commit 99cd3ea + addon de IA/prompts/CI |
| 1.1.0 | 2026-07-25 | Atualiza contagem de testes (68), adiciona `packages/catalog` (persistência real + wiring de tradução de gênero) ao score, corrige README/DEVOPS/BUSINESS_PLAN que descreviam persistência como inexistente |

## MELO vs. bases de indústria (ECAD / Discogs / ACRCloud / gravadoras)

Comparação de identificadores — não é sobre volume de dados, é sobre
**vocabulário compartilhado**: sem esses códigos, o MELO nunca casa
automaticamente com um registro real de ECAD/Discogs, mesmo que os dados
estejam corretos, porque cada sistema usa uma chave diferente pra "a
mesma coisa".

| Identificador | O que é | Quem usa | Status no MELO |
|---|---|---|---|
| ISRC | Gravação específica (fonograma) | ECAD, Discogs, ACRCloud, todo DSP | Campo adicionado (`faixas.isrc`), **não preenchido automaticamente** — precisa de fonte externa ou input manual |
| ISWC | Composição/obra (letra+melodia) | ECAD, CISAC | Campo adicionado (`faixas.iswc`), mesma limitação |
| ISNI | Pessoa física (artista/autor) | Discogs, bibliotecas, ECAD | Campo adicionado (`source_artists.isni`, `destination_artists.isni`) |
| IPI | Parte interessada pra royalty (CISAC) | ECAD diretamente | Campo adicionado (`source_artists.ipi_number`, `produtores.ipi_number`) |
| UPC/EAN | Release/álbum | Discogs, distribuidoras | Campo adicionado (`faixas.upc`) |
| DDEX Party ID | Empresa na cadeia B2B de distribuição | Distribuição digital moderna | Campo adicionado (`produtores.ddex_party_id`) |
| Fingerprint acústico (tipo ACRCloud `acrid`) | Match de áudio por conteúdo, não metadado | ACRCloud, Shazam-like | **Não existe.** `packages/catalog` casa por nome/path, não por conteúdo do áudio. Gap real, não é só campo faltando — exigiria motor de fingerprinting (fora de escopo atual). |

**Conclusão**: os campos foram adicionados (schema pronto pra receber os
códigos), mas **preenchê-los automaticamente é outro projeto** — exige
integração com uma base externa (Discogs API, ACRCloud, ou cadastro
manual/CRM via `packages/catalog/partners.py`, se for essa a peça que
resolve isso — não verificado nesta sessão). Sem essa integração, os
campos ficam `NULL` e o "formato de indústria" é só estrutural, não
funcional ainda.
