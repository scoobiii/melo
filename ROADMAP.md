# ROADMAP — MELO

Este roadmap reflete o estado real do código em `packages/` e a tabela de
status do README. Cada fase só avança quando a anterior tem testes verdes.

## Fase 0 — Núcleo técnico (CONCLUÍDA)

Estágio atual do projeto. Testes: 32, 100% verdes.

- [x] `packages/audio` — metadados de áudio (duração, sample rate, canais)
- [x] `packages/lyrics` — transcrição de letra via Whisper local
- [x] `packages/adaptation` — estimativa de BPM + correlação de gênero
      panamá ↔ brasil
- [x] `packages/pipeline` — orquestração audio → adaptation → lyrics
- [x] `packages/publisher` — motor de split/payout de royalty (percentuais
      definidos fora do código)

**Limitação conhecida**: MP3 não é lido diretamente, exige conversão prévia
para WAV via `ffmpeg`.

## Fase 1 — Geração de áudio (`packages/ai`, `packages/voices`)

Ainda não implementado. É o que falta para sair de "ferramenta de análise"
para "fábrica de adaptação" de fato.

- [ ] Modelo de síntese/regravação instrumental adaptado ao gênero-alvo
- [ ] Modelo de voz (clonagem ou síntese) respeitando licenciamento —
      ver aviso legal do README antes de qualquer integração com voz de
      artista real
- [ ] Pipeline de regeneração: entrada (faixa original) → saída (faixa
      adaptada), com controle de qualidade automatizado
- [ ] Testes de regressão de qualidade de áudio (não apenas de execução)

## Fase 2 — Score e prompts (`packages/score`, `packages/prompts`)

- [ ] Sistema de scoring de aderência ao gênero-alvo (quão "pisadinha" ficou
      uma faixa típica panamenha, por exemplo)
- [ ] Biblioteca de prompts para modelos de IA generativa usados na Fase 1
- [ ] Métrica de qualidade utilizável por humanos (não só binária pass/fail)

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
