# ROADMAP — MELO

Este roadmap reflete o estado real do código em `packages/` e a tabela de
status do README. Cada fase só avança quando a anterior tem testes verdes.

## Fase 0 — Núcleo técnico (CONCLUÍDA)

Estágio atual do projeto. Testes: 122, 100% verdes (contagem sincronizada
com README.md via scripts/generate_docs.py — não editar este número à mão).

- [x] `packages/audio` — metadados de áudio (duração, sample rate, canais)
      + validação (formato, tamanho, cache, lote)
- [x] `packages/lyrics` — transcrição de letra via faster-whisper local
- [x] `packages/adaptation` — estimativa de BPM + correlação de gênero
      panamá ↔ brasil + segmentação de letra e de mix multi-artista
- [x] `packages/pipeline` — orquestração audio → adaptation → lyrics
- [x] `packages/publisher` — motor de split/payout de royalty (percentuais
      definidos fora do código)
- [x] `packages/catalog` — persistência SQLite (artistas, produtores,
      faixas, vozes, mixes, parceiros de negócio) + wiring de tradução
- [x] `packages/ai`, `packages/prompts` — adaptação de letra via LLM +
      conceito de artista híbrido (hybrid_artist.py), sem I/O
- [x] `packages/score` — métrica de aderência não-binária

**Limitação conhecida**: MP3 não é lido diretamente, exige conversão prévia
para WAV via `ffmpeg`.

## Fase 1 — Geração de áudio (`packages/voices`)

Parcialmente implementado — é o que falta para sair de "ferramenta de
análise" para "fábrica de adaptação" de fato.

- [x] `InstrumentalAdapter` — time-stretch + EQ de textura (placeholder
      determinístico, não-generativo), testado (11 testes)
- [ ] Modelo de síntese/regravação instrumental generativo de verdade
      (o adapter atual é DSP simples, não IA generativa)
- [ ] Modelo de voz (clonagem ou síntese) respeitando licenciamento —
      `VoiceGenerator` já existe como contrato/skeleton: recusa gerar sem
      backend externo (RVC/Coqui/Bark) e cita a exigência de licença
      explícita no próprio erro. Ver aviso legal do README antes de
      qualquer integração com voz de artista real.
- [ ] Pipeline de regeneração: entrada (faixa original) → saída (faixa
      adaptada), com controle de qualidade automatizado
- [ ] Testes de regressão de qualidade de áudio (não apenas de execução)

## Fase 2 — Score e prompts (`packages/score`, `packages/prompts`)

- [x] Sistema de scoring de aderência ao gênero-alvo (correlação + confiança
      vocal + cobertura de dados, não-binário) — `packages/score`
- [x] Prompt engineering isolado sem I/O (system prompt, few-shot) para
      adaptação de letra e conceito de artista híbrido — `packages/prompts`
- [ ] Biblioteca de prompts ampliada para os modelos generativos da Fase 1
      (a Fase 2 atual cobre letra/conceito, não áudio)
- [ ] Métrica de qualidade validada com ouvintes humanos (hoje é heurística
      não validada musicologicamente)

## Fase 3 — Distribuição e licenciamento automatizado

Mencionado no README como excluído do escopo atual por design (não fazer
scraping/download não licenciado). Esta fase trata do que É permitido
automatizar:

- [ ] Integração com sistemas de licenciamento mecânico (ECAD ou
      equivalente, dependendo da jurisdição)
- [ ] Cálculo e registro automatizado de splits usando `packages/publisher`
      como motor
- [ ] Trilha de auditoria de licenciamento por faixa gerada

## Fase 4 — Produto

- [ ] Interface (`apps/web`, `apps/mobile`, ou `apps/cli`) usável por alguém
      que não seja desenvolvedor
- [ ] Onboarding de licenciamento (usuário precisa comprovar direito sobre
      a faixa original antes de gerar adaptação)
- [ ] Modelo de monetização definido em `BUSINESS_PLAN.md`

## Notas

- Este roadmap substitui o `ROADMAP.md` anterior, que existia como arquivo
  vazio (0 bytes) desde 21/07.
- Prioridade sugerida: Fase 1 antes de Fase 3, porque sem geração de áudio
  não há o que licenciar/distribuir.
