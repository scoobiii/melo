# BACKLOG — MELO

> Consolidação de pendências espalhadas por múltiplas seções do
> HANDOFF.md. Atualizar aqui quando um item for resolvido (mover pra
> "Concluído" com data e commit), e adicionar itens novos aqui direto —
> não deixar pendência nova só em prosa de handoff de novo.

## P0 — Bloqueadores reais do produto (nada avança sem isso)

1. **`packages/voices/generator.py` sem backend de voz real.**
   `InstrumentalAdapter` funciona (time-stretch/EQ, não-generativo);
   `VoiceGenerator` é skeleton, exige RVC/Coqui/Bark externo. Continua
   sendo o teto do produto — sem isso, "adaptação" não vira áudio novo.
2. **Validação com 1 titular de catálogo real.** Citado em toda sessão
   desde o BUSINESS_PLAN inicial. Nenhum código resolve isso — é ação
   humana (conversa com editora/artista), não engenharia.
3. **Fingerprinting em repertório de nicho é inconclusivo.** 1 teste real
   via AudD, não reconheceu a faixa típica panamenha. Sem isso, a
   identificação de artista em mixes de DJ (`identify_mix_track`) fica
   sem fonte de dado automatizada — depende de curadoria manual.

## P1 — Dívida técnica com impacto direto em confiabilidade

4. **`apps/api` não aparece na tabela de módulos do README/`generate_docs.py`.**
   11 testes da API ficam invisíveis na contagem documentada. Corrigir
   `generate_docs.py` pra varrer `apps/` também, não só `packages/`.
5. **`server.py` da API tem zero teste automatizado** (roteamento, 404,
   parsing de corpo vazio) — tudo validado só via `curl` manual até
   agora. ~6 testes faltando, listados em handoff de 27/07.
6. **~16 testes faltando nos endpoints da API** pra 100% de cobertura
   real (branches de filtro, campo faltando, casos de erro) — tabela
   completa por endpoint já existe no HANDOFF.md de 27/07, copiar de lá.
7. **`full_mix_analysis.py`**: (a) default de `--modelo` é `tiny`, devia
   ser `small` (tiny é pior qualidade); (b) não salva progresso
   incrementalmente, só grava JSON no final — risco real se o processo
   cair no meio de um mix longo.
8. **Alucinação conhecida do Whisper** (`"¡Suscríbete!"` em trechos
   instrumentais/silêncio) sem filtro — sugestão já registrada: descartar
   ou marcar `[MÚSICA]` transcrição contendo `suscríbete`/`subscribe`.

## P2 — Decisões de escopo pendentes (não é bug, é escolha)

9. **Swagger/OpenAPI da API**: sem FastAPI não vem grátis. Opções:
   `openapi.json` manual (~1h) ou página HTML estática. Decisão de
   escopo, ainda não tomada.
10. **`packages/publisher` precisa de 1 caso real de split negociado**
    pra fechar o gap de "percentuais só teóricos" — sem isso, o motor
    de royalty nunca foi testado contra número de negócio real.
11. **Tradução (`packages/ai`) nunca rodou com API key paga de verdade**
    — só testado com mock/key de teste.
12. **Instrumental isolado pra karaokê** (source separation, tipo
    Demucs/Spleeter/UVR) — identificado como necessário, não existe em
    nenhum módulo.

## Concluído recentemente (não reabrir sem motivo novo)

- ✅ whisper.cpp validado ponta-a-ponta com áudio real (27/07)
- ✅ `handle` (@) pra pessoas reais no catálogo, nunca automático/IA (27/07)
- ✅ Coluna `transcricao` em `mix_tracks` + `update_mix_track_transcricao` (27/07)
- ✅ FastAPI descartado (Rust/maturin não instala Termux) — API é stdlib puro (27/07)
- ✅ `vocal_profiles` + `digital_twins` com trava de consentimento (26/07 noite)
- ✅ HANDOFF.md consolidado em arquivo único (26/07)
- ✅ Scripts de sprint órfãos removidos/arquivados em `archive/session_scripts/`
- ✅ `claim_handle` rejeitava @ duplicado só na documentação — faltava UNIQUE INDEX; corrigido + teste de regressão (28/07, commit 784ca0a)
- ✅ `HANDOFF.md` limpo — conteúdo não-técnico movido pra `notes/` (28/07, commit 0aeb644)
- ✅ Testes de API (`test_api_handlers_extra.py`, `test_api_server.py`) commitados, incluindo fix de rota `/mix-tracks/{id}/escrow` (28/07, commit 2556aca)

## Notas de processo (não são tarefas, são regras já validadas)

- Migração idempotente checa **resultado** (`PRAGMA table_info` /
  `"def novo_metodo" in src`), nunca âncora de texto de inserção.
- `cat` real antes de editar qualquer arquivo não commitado.
- Scripts de migração não fazem `git push` automático — só até o commit,
  revisão manual do diff antes.
- `/tmp` não é confiável no Termux — usar `$HOME/algum_dir`.
- Nenhum framework com dependência Rust/Cython nativa (torch, av,
  pydantic-core/FastAPI, jiter/anthropic SDK) — todos falharam neste
  ambiente. Preferir stdlib ou C puro compilado localmente (whisper.cpp).
