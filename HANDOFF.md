# HANDOFF — sessão de 25-26/07, nick `tamborito`

Documento de passagem de bastão. Se você é o próximo dev (humano ou outra
sessão do Claude) trabalhando neste repo, comece por aqui.

## Estado real, confirmado (não achismo)

Commits desta sessão, em ordem, todos em `main` no remoto:

```
0b73728 feat(prompts): artista híbrido
6d32475 docs: atualiza tabela de módulos do README
de9ae2c refactor(lyrics): migra de openai-whisper para faster-whisper
eedde00 test(voices): cobertura para InstrumentalAdapter e VoiceGenerator
48c5a36 fix(voices): adapt() aceita e propaga source_genre/target_genre
b9d870e test(voices): atualiza teste do bug pro fix aplicado
6f968ac chore(voices): adiciona __init__.py do pacote
```

Suíte completa (última vez rodada): **119 passed, 2 failed** em
`tests/test_audio_validate.py` (`test_file_too_large`,
`test_batch_validation_performance`).

## Pendência #1 — EM ANDAMENTO, patch pronto mas não aplicado

`packages/audio/validate.py` e `tests/test_audio_validate.py` **nunca foram
commitados** — ainda aparecem como `??` (untracked) no `git status`. Os 2
testes falhando são bug do teste, não do código-fonte:

- `test_file_too_large`: tenta `path.stat = lambda: ...`, que quebrou no
  Python 3.14 (`Path.stat` virou read-only). Fix: usar `monkeypatch.setattr`
  em `os.stat`, não atribuição direta na instância.
- `test_batch_validation_performance`: passa o mesmo path 5x esperando 5
  resultados, mas `validate_batch` deduplica por path (comportamento
  intencional, aproveitando o cache de `validate_file`). Fix: reescrever
  usando 5 arquivos distintos + um teste novo documentando a deduplicação
  como comportamento esperado (não bug).

**O patch completo (dois métodos reescritos + um teste novo) está na
mensagem do Claude anterior a este handoff, na conversa. Copie de lá.**
Depois de aplicar:

```bash
cd ~/MELO
pytest tests/test_audio_validate.py -v   # esperado: 13 passed
git add packages/audio/validate.py tests/test_audio_validate.py
git commit -m "fix(audio): corrige testes de validate.py incompatíveis com Python 3.14

test_file_too_large usava atribuição direta em Path.stat, que virou
read-only no 3.14 — trocado por monkeypatch.setattr em os.stat.
test_batch_validation_performance esperava 5 resultados de 5 paths
repetidos; validate_batch deduplica por path intencionalmente (mesmo
cache de validate_file) — reescrito com 5 arquivos distintos, e
adicionado teste novo documentando a deduplicação como esperada."
git push origin main
```

## Pendência #2 — pronta pra commitar, sem bloqueio

`tests/unit/test_catalog_mixes.py` já está 7/7 verde. Só falta:

```bash
cd ~/MELO
git add tests/unit/test_catalog_mixes.py
git commit -m "test(catalog): testes de mixes/mix_tracks (add_mix, identificação por confiança, filtro)"
git push origin main
```

## Pendência #3 — decisão ainda não tomada

Scripts de reorganização (`reorganize_scripts.sh`, `cleanup_dev_scripts.sh`)
ainda não foram rodados. `fix_repo_layout.sh` (que causava a divergência
entre os dois) já foi **deletado** — não estava versionado, não afeta
histórico. Os dois scripts restantes devem ser compatíveis agora, mas
**ninguém rodou nenhum dos dois ainda nesta sessão** — revisar
`cleanup_dev_scripts.sh` com atenção ao `.gitignore` (ele usa `fix_*.sh`
sem `/` na frente — sugestão pendente de ancorar como `/fix_*.sh` pra não
vazar pra dentro de `scripts/fix/` depois do reorganize).

## Pendência #4 — não iniciada

README.md e ROADMAP.md continuam com contagens de teste desatualizadas
(README já foi parcialmente corrigido no commit `6d32475`, mas o número
total ainda não reflete os +11 de voices, +7 de catalog_mixes, e o que
vier de audio_validate). ROADMAP.md **nunca foi corrigido** — ainda diz
que `packages/catalog`, `packages/score`, `packages/ai`/`prompts` estão
"não implementados", o que é falso (estão implementados e testados).
Patch sugerido já foi escrito numa mensagem anterior desta conversa —
copiar de lá.

## Untracked ainda sem revisão nesta sessão

```
extend_catalog_translation.sh
implement_score.sh
migrate_to_whisper_cpp.sh
sync_and_version.sh
sync_docs_with_catalog.sh
sync_prompts_score_docs.sh
update_readme_decision.sh
```

Nenhum desses foi lido ainda. Antes de rodar qualquer um, `cat` primeiro —
foi o padrão que funcionou bem nesta sessão (achamos bug real de
duplicata em `requirements/ai.txt` só por ler antes de rodar).

## Lição aprendida nesta sessão (documentando pra não repetir)

Um heredoc (`cat > arquivo << 'EOF' [placeholder] EOF`) foi colado com um
placeholder literal em vez do conteúdo real, sobrescrevendo
`packages/voices/generator.py` (que ainda não estava commitado, sem rede
de segurança). Foi recuperado porque o conteúdo tinha sido colado em
mensagem anterior da conversa. **Regra daqui pra frente: nunca editar via
heredoc um arquivo ainda não commitado sem antes rodar `git add` +
`git commit` de um checkpoint, mesmo que "provisório".** Preferir `nano`
pra edições grandes coladas manualmente.

---

# HANDOFF — sessão adicional (agente: Claude via chat, sem Claude Code)

## Contexto importante pro próximo agente

Esta sessão rodou em paralelo/depois de outra sessão (provavelmente Claude
Code direto no terminal) que avançou bastante sem visibilidade mútua:
implementou `packages/voices`, CRM (`catalog/partners.py`), mixes,
migrou lyrics pra whisper.cpp, e criou `generate_docs.py` pra gerar
README/DEVOPS automaticamente. Esta sessão (chat) tinha feito
`packages/catalog` (produtores/faixas/vozes/translation) e
`packages/score` antes da divergência — commit `bd98ded` é o ponto onde
as duas linhas do trabalho se encontram no histórico.

**Lição confirmada de novo nesta sessão**: um `HANDOFF.md` anterior citava
"o patch está numa mensagem anterior desta conversa" — mas essa "conversa"
era de uma sessão diferente (Claude Code), não a que estava lendo o
handoff. Esta sessão não reescreveu esse patch de memória.

**Segunda lição desta sessão**: script assumiu `/tmp` como diretório
temporário válido — Termux/Android não garante isso (sandboxing). Usar
`$HOME/algum_dir` ou `mktemp` com `TMPDIR` explícito, nunca `/tmp`
hardcoded, em qualquer script futuro pra este ambiente.

## O que esta sessão fez, confirmado

- Commitou `tests/unit/test_catalog_mixes.py`.
- Removeu scripts órfãos que já tinham cumprido o papel:
  `extend_catalog_translation.sh`, `implement_score.sh`,
  `sync_docs_with_catalog.sh`, `sync_prompts_score_docs.sh`,
  `migrate_to_whisper_cpp.sh`, `update_readme_decision.sh`.
- **Não tocou** em `packages/audio/validate.py` nem
  `tests/test_audio_validate.py` — ver resultado real do pytest abaixo.
- **Não escreveu** o resumo "SWOT 3/3 por perfil" pedido — ficaria baseado
  em números desatualizados. Fica pro próximo agente, com
  `generate_docs.py` e `packages/voices/` lidos primeiro.

## Estado real da suíte nesta sessão (não estimado)

```
2 failed, 119 passed in 5.36s
```
Detalhe completo ficou em `$HOME/melo_tmp/full_suite_result.txt` nesta
sessão (não persiste entre sessões — rode a suíte de novo se precisar).

## Próximo passo recomendado (ordem)

1. Ler `generate_docs.py` — se já gera README/DEVOPS automaticamente,
   qualquer edição manual futura deve checar se não será sobrescrita.
2. Resolver Pendência #1 do handoff anterior (`audio/validate.py`) — com
   diagnóstico a confirmar rodando o teste, não a copiar de memória.
3. SÓ DEPOIS, recalcular o SWOT 3/3 por perfil que Zika pediu — com
   `voices` já existindo, o gap muda bastante e merece dado real.

---

# HANDOFF — fechamento sessão de chat [chat-session], 26/07 14:30

## SWOT 3/3 — % nesta sessão

Bruto ~87% (122 testes, catalog+lyrics endurecidos com bugs reais
corrigidos: dataclass regression, encoding UTF-8, env var persistente).
Ponderado por importância: continua **30-35%** — sem mudança de
categoria. Nenhum trabalho desta sessão tocou os dois bloqueadores reais
(`voices`/geração de voz e licenciamento automatizado, ambos 0/3).
Campos ISRC/ISWC/ISNI/IPI/UPC/DDEX adicionados ao catalog são estrutura
(schema pronto), não função (nada preenche automaticamente ainda).

## Commit HEAD desta sessão

```
376b2cbb2ea4ccf97ff10a35a5d7af3c8b442b1c
```

## Recado pro próximo GoS7

1. `cleanup_dev_scripts.sh`/`reorganize_scripts.sh` continuam sem
   serem lidos por nenhuma sessão até agora — ler antes de rodar.
2. Sessões de chat e Claude Code divergiram sem visibilidade mútua
   várias vezes nesta madrugada. Sempre `git log --oneline -15`,
   `git status`, `cat .gitignore` antes de confiar em qualquer
   HANDOFF.md — inclusive este.
3. Env vars (`WHISPER_CPP_BIN`, `WHISPER_CPP_MODEL_DIR`) precisam
   estar no `~/.bashrc` pra persistir entre sessões de shell — `export`
   avulso na sessão não sobrevive à próxima invocação de script.
4. **Separação vocal (source separation, tipo Demucs/Spleeter/UVR)**
   é peça nova identificada nesta sessão, necessária pro caso de uso de
   karaokê que surgiu na conversa — não existe em nenhum módulo atual.
   `InstrumentalAdapter` adapta BPM/textura do mix inteiro, não separa
   voz de instrumental.
5. `packages/publisher` segue precisando de 1 caso real de split
   negociado pra fechar o gap de 33% que já é conhecido há várias
   sessões.
6. Bloqueador de sempre, repetido porque continua verdadeiro: validar
   licenciamento com 1 titular de catálogo real antes de investir mais
   em `voices`/licenciamento — nenhum dos dois avança só com código.

## Nota sobre atribuição de sessão

Todos os commits desta conversa foram atribuídos a
`scoobiii <sobrinhosj@gmail.com>`, não a um nick de agente de IA —
Claude (Anthropic) não tem persona fixa entre sessões nem avatar
próprio, e não deveria entrar como "contribuidor" nomeado no mesmo
sentido que um dev humano no squad. Se for útil distinguir origem de
sessão em commits/handoffs futuros, sugestão é um marcador neutro no
início da mensagem (`[chat-session]` vs `[claude-code]`), não uma
identidade de personagem.
