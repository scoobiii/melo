# MELO — Music Adaptation Factory

Plataforma de análise, transcrição e adaptação musical entre gêneros regionais
(atualmente: raízes panamenhas — típico, cumbia, tamborito — correlacionadas
com gêneros brasileiros de tradição regional: forró, pisadinha, vanerão,
sertanejo em suas variantes).

## Status do projeto

Estágio: **núcleo técnico funcional, validado com áudio real**. Ainda não é
produto (sem geração/regravação de áudio, sem distribuição/licenciamento
automatizado). Ver [ROADMAP.md](./ROADMAP.md).

<!-- BEGIN:MODULES -->
| Módulo | O que faz | Testes |
|---|---|---|
| `packages/audio` | Metadados de áudio (duração, sample rate, canais) | 2 |
| `packages/lyrics` | Transcrição de letra via Whisper (local) | 5 |
| `packages/adaptation` | Estimativa de BPM, correlação de gênero panamá↔brasil e segmentação de letra | 24 |
| `packages/catalog` | Persistência (SQLite) de artistas/produtores/faixas/vozes + wiring de tradução de gênero | 27 |
| `packages/pipeline` | Orquestra audio → adaptation → lyrics numa chamada só | 4 |
| `packages/publisher` | Motor de split/payout de royalty (percentuais negociados fora do código) | 8 |
| `packages/ai`, `packages/prompts` | Adaptação de letra via LLM: prompt engineering isolado sem I/O (system prompt, few-shot) + client Anthropic API (retries, parsing XML) | 10 |
| `packages/score` | Métrica de aderência não-binária (correlação de gênero + confiança vocal + cobertura de dados) | 9 |
| `packages/voices` | Ainda não implementado | 0 |

**Total: 89 testes, suíte 100% verde.**
<!-- END:MODULES -->

## Quickstart

```bash
# instalar dependências mínimas
pip install soundfile numpy scipy pytest --break-system-packages

# rodar a suíte de testes
make test

# rodar o pipeline sobre um arquivo de áudio real
python scripts/run_pipeline.py caminho/faixa.wav --genero tipico_panameno
```

MP3 não é lido diretamente (ver [docs/USER_GUIDE.md](./docs/USER_GUIDE.md#formatos-de-áudio)) —
converta para WAV com `ffmpeg` antes.

## Aviso legal — fontes de áudio

Este projeto **não inclui, e não deve incluir**, qualquer mecanismo de
extração/download de áudio de plataformas de streaming (SoundCloud, YouTube,
Spotify etc.) sem licença. Ouvir uma faixa gratuitamente numa plataforma não
concede direito de reprodução/distribuição. Regravações ("covers") exigem
licença mecânica (no Brasil, via ECAD/editora) antes de qualquer uso
comercial. Ver [docs/USER_GUIDE.md](./docs/USER_GUIDE.md#fontes-de-áudio-legítimas).

## Documentação

- [docs/USER_GUIDE.md](./docs/USER_GUIDE.md) — como rodar o pipeline, formatos suportados, interpretação do output
- [docs/DEVOPS.md](./docs/DEVOPS.md) — ambiente, dependências, testes, estrutura dos módulos
- [BUSINESS_PLAN.md](./BUSINESS_PLAN.md), [ROADMAP.md](./ROADMAP.md)
