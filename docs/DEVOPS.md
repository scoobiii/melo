# DevOps / Ambiente — MELO

## Ambiente de desenvolvimento validado

- Termux (Android ARM64), Python 3.14.6
- `ffmpeg` 8.1.2 (build completo, com libx264/265, vulkan, neon)
- Testado em Samsung A23 (referência de hardware mínimo)

## Dependências

Divididas por domínio em `requirements/*.txt` (ai, audio, base, colab, dev,
music, termux, test). Instaladas incrementalmente conforme cada módulo foi
implementado — hoje o mínimo funcional é:

```bash
pip install soundfile numpy scipy pytest --break-system-packages
```

`openai-whisper` (usado por `packages/lyrics`) é **opcional** — o pipeline
degrada graciosamente sem ele (reporta erro de transcrição, não quebra).
**Atenção:** `openai-whisper` traz `torch` como dependência; builds de torch
para Android ARM64 são instáveis/inexistentes em muitos casos. Não incluído
automaticamente nos scripts de bootstrap por esse motivo.

Deliberadamente evitado: `librosa`/`numba`/`llvmlite` (build historicamente
instável em Termux ARM64). A estimativa de BPM usa autocorrelação simples
via `numpy`/`scipy` puro (`packages/adaptation/features.py`) em vez de
`librosa.beat`.

## Estrutura de módulos

```
packages/
├── audio/        # I/O e metadados de áudio (soundfile)
├── lyrics/       # transcrição via Whisper (import lazy, opcional)
├── adaptation/   # BPM + correlação de gênero panamá↔brasil + segmentação de letra
├── catalog/      # persistência SQLite: artistas, produtores, faixas, vozes,
                   # mapeamento de segmentos, wiring de tradução de gênero (translation.py)
├── pipeline/     # orquestra audio+lyrics+adaptation numa chamada
├── publisher/    # split/payout de royalty (percentuais não hardcoded)
├── ai/           # adapter de letra via LLM (prompt building, parsing, retries)
├── prompts/      # não implementado
├── score/        # não implementado (arranjo/partitura)
└── voices/       # não implementado
```

Cada módulo segue o padrão: `__init__.py` reexportando a API pública,
lógica em arquivo(s) próprio(s), testes espelhados em `tests/unit/`.

## Testes

```bash
make test          # roda pytest
make coverage       # roda com --cov
pytest -k adaptation  # roda só um módulo
```

Estado atual: 68 testes, 100% passando. `tests/integration` e
`tests/regression` existem como diretórios mas ainda não têm testes —
próximo débito técnico a endereçar (o pipeline foi validado manualmente
contra 1 arquivo de áudio real, não há teste de integração automatizado
com fixture de áudio real ainda).

## CI/CD

**Não configurado ainda.** Não há `.github/workflows/`. `Dockerfile` e
`docker-compose.yml` existem no repo mas não foram testados neste ciclo de
desenvolvimento — validar antes de assumir que buildam.

## Scripts de bootstrap

Os módulos foram criados via scripts idempotentes (`bootstrap_*.sh`,
`patch_*.sh`) que escrevem os arquivos, ajustam config quando necessário
e rodam a suíte de testes ao final. Eles não estão versionados dentro de
`scripts/` — ficaram na raiz do projeto durante o desenvolvimento
incremental. Considerar mover para `scripts/bootstrap/` e versionar, já
que documentam o histórico de como cada módulo foi construído.

## Limitações conhecidas (não escondidas, para não distorcer avaliação técnica)

- BPM: heurística por autocorrelação, não validada contra dataset musicológico
- Correlação de gênero: tabela curada manualmente, não validada com especialistas
- Transcrição: nunca testada com Whisper real neste ambiente (só mockado)
- `packages/adaptation` analisa janela fixa de 40s — não segmenta mixes/playlists automaticamente
- `packages/publisher` não tem percentuais de exemplo "de mercado" — decisão deliberada para não sugerir números não negociados
