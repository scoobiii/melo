# HANDOFF — MELO

> Convenção: UM arquivo só. Cada sessão/sprint acrescenta uma seção
> nova NO TOPO (mais recente primeiro), nunca cria handoff_2.md,
> handoff_addendum.md, etc. Se o arquivo ficar longo demais,
> arquivar seções antigas em docs/handoff-archive/AAAA-MM.md,
> mas o arquivo ativo continua sendo só HANDOFF.md.

---

# HANDOFF — fechamento sessão de chat [chat-session], 26/07 (continuação)

## Dúvidas que esta sessão levantou e já resolveu (não deixar reabrir)

| Dúvida | Resposta confirmada | Como foi confirmado |
|---|---|---|
| `faster-whisper` funciona no Termux? | **Não.** Dependência `av` falha ao compilar — erro de incompatibilidade Cython `noexcept` contra Python 3.14, não relacionado a ARM/Rust. | `pip install faster-whisper` até o fim, traceback completo colado na conversa |
| `whisper.cpp` funciona no Termux? | **Sim.** Compila com `clang`/`cmake` já presentes, sem tocar torch. | Build completo até `whisper-cli`, rodado contra áudio real, texto coerente com modelo `small` |
| `small` vs `base` vs `large-v3`, qual usar? | **`small` local.** `base` alucina demais; `large-v3` exige GPU (Colab) que contradiz a meta de 350MB de RAM já declarada em `packages/audio/validate.py`. | Comparação lado a lado no mesmo trecho de 15s; teste de `large-v3` no Colab deu `OutOfMemoryError` numa GPU de 14GB |
| Colab vale o esforço pra este projeto? | **Não, veredito fechado nesta sessão ("colab lixo").** OOM, kernel restart, rate limit de HF, resultado nunca confirmado até o fim — tudo pra um ganho de qualidade que a arquitetura do projeto não pede (meta é rodar local, 350MB). | Sequência completa de erros na conversa; nenhuma transcrição via Colab foi confirmada de ponta a ponta |
| Bug do `test_file_too_large` era o que o handoff anterior descrevia? | Parcialmente — o teste passou 13/13 sem precisar de correção adicional. A hipótese de `follow_symlinks` levantada nesta sessão **era especulação errada**, corrigida ao rodar o teste real. | `pytest tests/test_audio_validate.py -v` → 13 passed |
| Custo de fingerprinting (ACRCloud/AudD) inviabiliza o produto? | **Não** — ~R$0,03–0,04 por faixa identificada. Mas **qualidade em repertório de nicho (típico panamenho) é inconclusiva** — 1 teste real, não reconheceu. | Pesquisa de preço + 1 chamada real à API AudD |
| `packages/voices` está mesmo 0% implementado? | **Refinado, não invalidado.** `InstrumentalAdapter` é funcional (time-stretch real via scipy). `VoiceGenerator` levanta erro sem backend — geração de voz de fato segue não implementada. | Leitura do `generator.py` real, colado na conversa |
| Existe trabalho paralelo de outra sessão/agente no mesmo repo? | **Sim, confirmado repetidas vezes** — CRM (`catalog/partners.py`), `catalog/translation.py`, `score/quality.py`, `integrations/{crm,erp,legal_signing}`, `prompts/hybrid_artist.py`, `generate_docs.py`, e o próprio `HANDOFF.md` com múltiplas sessões anteriores documentadas. | `tree packages/`, `cat HANDOFF.md` |

## Lições de casa pra quem assumir o próximo sprint

1. **Nunca editar ou substituir um arquivo sem `cat` real dele primeiro**, mesmo que pareça óbvio pelo nome dos testes. Aconteceu 2x nesta linha de sessões (uma vez comigo, sobrescrevendo `catalog/store.py`; uma vez em sessão anterior, sobrescrevendo `voices/generator.py` via heredoc com placeholder literal). As duas foram recuperadas porque o conteúdo real tinha sido colado em algum ponto da conversa — **isso é sorte, não processo**. Trate qualquer arquivo não commitado como sem rede de segurança.

2. **Rode antes de afirmar.** Nesta sessão, uma hipótese de bug (`follow_symlinks` em `Path.stat`) foi levantada por especulação e estava errada — só descobrimos porque rodamos o teste real em vez de confiar no raciocínio. Regra: qualquer afirmação sobre comportamento de código deve vir acompanhada do comando que a comprova, ou marcada explicitamente como hipótese não testada.

3. **A meta de 350MB de RAM já existe e não foi respeitada por boa parte desta sessão.** `packages/audio/validate.py` declara essa restrição desde antes desta sessão. Qualquer decisão futura de modelo (Whisper, voz, fingerprinting) precisa checar esse teto primeiro — Colab/GPU remota é desalinhado com a arquitetura pretendida do projeto (rodar local, no dispositivo do usuário), não é só "mais lento".

4. **`generate_docs.py` conta testes por glob de nome de arquivo, não por import/AST.** Um arquivo de teste que não segue a convenção `test_<pacote>_*.py` fica invisível na contagem, mesmo passando na suíte real. Já causou divergência de 76 vs 89 testes documentados uma vez nesta linha de sessões. Sempre rodar `pytest tests/ -v | tail` e comparar com o total que `generate_docs.py` reporta antes de confiar no README.

5. **Sessões em paralelo (chat vs. Claude Code vs. outro agente) divergem sem visibilidade mútua.** Confirmado múltiplas vezes nesta linha de handoffs. Antes de confiar em qualquer HANDOFF.md — inclusive este — rodar `git log --oneline -20`, `git status`, e comparar com o que o handoff afirma.

6. **Scripts que fazem `git commit && git push` sozinhos no final merecem uma pausa manual antes do push**, mesmo quando tecnicamente bem escritos (com verificação de âncora, teste embutido, etc. — caso de `add_industry_ids.sh`, ainda não executado nesta sessão). Automação de commit é aceitável; automação de push sem revisão humana do diff não.

7. **Nunca colar API key real em texto puro no chat.** Aconteceu 2x nesta sessão com a key do AudD (trial, risco baixo por não ter billing, mas o hábito é o problema, não o caso específico).

8. **`/tmp` não é diretório temporário confiável no Termux/Android** (sandboxing). Usar `$HOME/algum_dir` ou `mktemp` com `TMPDIR` explícito.

## Itens em aberto, não resolvidos por esta sessão

- `add_industry_ids.sh`: revisado, não executado. Recomendação registrada: remover o `git push` automático do final antes de rodar.
- `cleanup_dev_scripts.sh` / `reorganize_scripts.sh`: seguem sem leitura por nenhuma sessão até agora.
- `send_to_colab.sh` / `fetch_from_colab.sh`: tecnicamente seguros (só `rclone copy` de/para pastas fixas), mas o caminho Colab como um todo foi descartado nesta sessão — ficam como código morto documentado, não como fluxo recomendado.
- Fingerprinting de faixa em repertório de nicho: inconclusivo, só 1 teste real rodado.
- Identificação automática de ISRC/ISWC/ISNI/etc. (schema pronto via `add_industry_ids.sh`, quando/se rodado): preenchimento automático continua sendo outro projeto, não resolvido por adicionar a coluna.
- `voices/generator.py`: interface pronta, zero backend de voz real plugado. Continua sendo o gargalo central do produto.
- Validação com 1 titular de catálogo real: segue não feita, é bloqueador citado em múltiplas sessões anteriores a esta.

---

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
# HANDOFF — fechamento sessão de chat [chat-session], 26/07 (continuação)

## Dúvidas que esta sessão levantou e já resolveu (não deixar reabrir)

| Dúvida | Resposta confirmada | Como foi confirmado |
|---|---|---|
| `faster-whisper` funciona no Termux? | **Não.** Dependência `av` falha ao compilar — erro de incompatibilidade Cython `noexcept` contra Python 3.14, não relacionado a ARM/Rust. | `pip install faster-whisper` até o fim, traceback completo colado na conversa |
| `whisper.cpp` funciona no Termux? | **Sim.** Compila com `clang`/`cmake` já presentes, sem tocar torch. | Build completo até `whisper-cli`, rodado contra áudio real, texto coerente com modelo `small` |
| `small` vs `base` vs `large-v3`, qual usar? | **`small` local.** `base` alucina demais; `large-v3` exige GPU (Colab) que contradiz a meta de 350MB de RAM já declarada em `packages/audio/validate.py`. | Comparação lado a lado no mesmo trecho de 15s; teste de `large-v3` no Colab deu `OutOfMemoryError` numa GPU de 14GB |
| Colab vale o esforço pra este projeto? | **Não, veredito fechado nesta sessão ("colab lixo").** OOM, kernel restart, rate limit de HF, resultado nunca confirmado até o fim — tudo pra um ganho de qualidade que a arquitetura do projeto não pede (meta é rodar local, 350MB). | Sequência completa de erros na conversa; nenhuma transcrição via Colab foi confirmada de ponta a ponta |
| Bug do `test_file_too_large` era o que o handoff anterior descrevia? | Parcialmente — o teste passou 13/13 sem precisar de correção adicional. A hipótese de `follow_symlinks` levantada nesta sessão **era especulação errada**, corrigida ao rodar o teste real. | `pytest tests/test_audio_validate.py -v` → 13 passed |
| Custo de fingerprinting (ACRCloud/AudD) inviabiliza o produto? | **Não** — ~R$0,03–0,04 por faixa identificada. Mas **qualidade em repertório de nicho (típico panamenho) é inconclusiva** — 1 teste real, não reconheceu. | Pesquisa de preço + 1 chamada real à API AudD |
| `packages/voices` está mesmo 0% implementado? | **Refinado, não invalidado.** `InstrumentalAdapter` é funcional (time-stretch real via scipy). `VoiceGenerator` levanta erro sem backend — geração de voz de fato segue não implementada. | Leitura do `generator.py` real, colado na conversa |
| Existe trabalho paralelo de outra sessão/agente no mesmo repo? | **Sim, confirmado repetidas vezes** — CRM (`catalog/partners.py`), `catalog/translation.py`, `score/quality.py`, `integrations/{crm,erp,legal_signing}`, `prompts/hybrid_artist.py`, `generate_docs.py`, e o próprio `HANDOFF.md` com múltiplas sessões anteriores documentadas. | `tree packages/`, `cat HANDOFF.md` |

## Lições de casa pra quem assumir o próximo sprint

1. **Nunca editar ou substituir um arquivo sem `cat` real dele primeiro**, mesmo que pareça óbvio pelo nome dos testes. Aconteceu 2x nesta linha de sessões (uma vez comigo, sobrescrevendo `catalog/store.py`; uma vez em sessão anterior, sobrescrevendo `voices/generator.py` via heredoc com placeholder literal). As duas foram recuperadas porque o conteúdo real tinha sido colado em algum ponto da conversa — **isso é sorte, não processo**. Trate qualquer arquivo não commitado como sem rede de segurança.

2. **Rode antes de afirmar.** Nesta sessão, uma hipótese de bug (`follow_symlinks` em `Path.stat`) foi levantada por especulação e estava errada — só descobrimos porque rodamos o teste real em vez de confiar no raciocínio. Regra: qualquer afirmação sobre comportamento de código deve vir acompanhada do comando que a comprova, ou marcada explicitamente como hipótese não testada.

3. **A meta de 350MB de RAM já existe e não foi respeitada por boa parte desta sessão.** `packages/audio/validate.py` declara essa restrição desde antes desta sessão. Qualquer decisão futura de modelo (Whisper, voz, fingerprinting) precisa checar esse teto primeiro — Colab/GPU remota é desalinhado com a arquitetura pretendida do projeto (rodar local, no dispositivo do usuário), não é só "mais lento".

4. **`generate_docs.py` conta testes por glob de nome de arquivo, não por import/AST.** Um arquivo de teste que não segue a convenção `test_<pacote>_*.py` fica invisível na contagem, mesmo passando na suíte real. Já causou divergência de 76 vs 89 testes documentados uma vez nesta linha de sessões. Sempre rodar `pytest tests/ -v | tail` e comparar com o total que `generate_docs.py` reporta antes de confiar no README.

5. **Sessões em paralelo (chat vs. Claude Code vs. outro agente) divergem sem visibilidade mútua.** Confirmado múltiplas vezes nesta linha de handoffs. Antes de confiar em qualquer HANDOFF.md — inclusive este — rodar `git log --oneline -20`, `git status`, e comparar com o que o handoff afirma.

6. **Scripts que fazem `git commit && git push` sozinhos no final merecem uma pausa manual antes do push**, mesmo quando tecnicamente bem escritos (com verificação de âncora, teste embutido, etc. — caso de `add_industry_ids.sh`, ainda não executado nesta sessão). Automação de commit é aceitável; automação de push sem revisão humana do diff não.

7. **Nunca colar API key real em texto puro no chat.** Aconteceu 2x nesta sessão com a key do AudD (trial, risco baixo por não ter billing, mas o hábito é o problema, não o caso específico).

8. **`/tmp` não é diretório temporário confiável no Termux/Android** (sandboxing). Usar `$HOME/algum_dir` ou `mktemp` com `TMPDIR` explícito.

9. **Um script "idempotente" que checa a âncora de inserção errada não é idempotente de verdade.** Incidente real desta sessão: `add_industry_ids.sh` verificava se a string-âncora `def _init_schema... conn.executescript(_SCHEMA)` existia no arquivo antes de inserir a migração. Mas essa âncora **continua presente mesmo depois da migração já ter sido aplicada** (o código novo foi inserido *antes* dela, não a substituiu) — então rodar o script uma segunda vez inseriu o método `_apply_industry_id_migrations` de novo, duplicado, com uma chamada recursiva a si mesmo na cópia nova. Os testes passaram mesmo assim porque Python usa a última definição de método com aquele nome numa classe (a antiga, sem o bug), mascarando o problema até alguém olhar o `git diff` com atenção.
   **Regra geral**: script de migração idempotente precisa checar **o resultado da migração** (o método/coluna já existe?), nunca **o ponto de inserção** (a âncora de texto onde o código seria colocado). Âncora de inserção quase sempre segue presente depois de já ter sido usada — checar ela só prova que aquele ponto do arquivo existe, não que a mudança já foi feita. Verificação correta seria `grep -c "def _apply_industry_id_migrations" "$STORE"` (aborta se ≥1) ou, melhor, `PRAGMA table_info` direto no banco.

## Incidente aberto — bug de duplicação em `packages/catalog/store.py` (não commitado)

Rodar `add_industry_ids.sh` (mesmo a versão sem auto-push) numa segunda vez sobre um arquivo que já tinha a migração aplicada por outra sessão gerou `_apply_industry_id_migrations` duplicado na classe `CatalogStore`, com recursão infinita na definição nova (mascarada pela definição antiga, que o Python usa por último). **Não foi commitado** — `git diff` foi revisado antes do commit, é exatamente pra isso que a parada manual do script existe. Próximo passo: `grep -n "_apply_industry_id_migrations" packages/catalog/store.py` pra localizar as duas definições exatas, remover o bloco duplicado (mantendo a versão antiga/funcional), rodar a suíte de novo, só então commitar.

## Itens em aberto, não resolvidos por esta sessão

- `add_industry_ids.sh`: revisado, não executado. Recomendação registrada: remover o `git push` automático do final antes de rodar.
- `cleanup_dev_scripts.sh` / `reorganize_scripts.sh`: seguem sem leitura por nenhuma sessão até agora.
- `send_to_colab.sh` / `fetch_from_colab.sh`: tecnicamente seguros (só `rclone copy` de/para pastas fixas), mas o caminho Colab como um todo foi descartado nesta sessão — ficam como código morto documentado, não como fluxo recomendado.
- Fingerprinting de faixa em repertório de nicho: inconclusivo, só 1 teste real rodado.
- Identificação automática de ISRC/ISWC/ISNI/etc. (schema pronto via `add_industry_ids.sh`, quando/se rodado): preenchimento automático continua sendo outro projeto, não resolvido por adicionar a coluna.
- `voices/generator.py`: interface pronta, zero backend de voz real plugado. Continua sendo o gargalo central do produto.
- Validação com 1 titular de catálogo real: segue não feita, é bloqueador citado em múltiplas sessões anteriores a esta.
# HANDOFF — fechamento sessão de chat, 26/07 noite

## Estado real confirmado nesta sessão (não estimado)

- `scripts/full_mix_analysis.py` revisado (código real, não suposição):
  segmenta + transcreve num script só, via `soundfile` (sem depender de
  ffmpeg), mas **não salva progresso incrementalmente** (só grava o JSON
  no final do loop inteiro) e usa `--modelo tiny` como default — risco se
  cair no meio de um mix longo, e qualidade pior que `small` se rodado
  sem o parâmetro explícito.
- Rodada real de produção usou `--modelo small` explícito, terminou com
  sucesso: **175 segmentos**, `output/tipico_mix_vol2_dj_phantom.json`
  populado. Amostra dos 5 primeiros mostrou qualidade boa/coerente em
  português/espanhol, com uma exceção reconhecível: `"¡Suscríbete!
  ¡Suscríbete!"` no segmento 1 — **alucinação documentada do Whisper**,
  padrão de treino em dados do YouTube que "ouve" pedidos de inscrição em
  trechos de silêncio/instrumental puro. Sugestão de filtro futuro:
  descartar/marcar como `[MÚSICA]` qualquer transcrição contendo
  `suscríbete`/`subscribe`/variantes.
- `packages/catalog/store.py` estendido com `vocal_profiles` (tessitura +
  textura + nível, taxonomia fechada) e `digital_twins` (gêmeo digital
  licenciado, com trava de código que impede `ativo=True` sem
  `status_consentimento='licenciado'`). Aplicado via
  `scripts/add_vocal_profiles.py`, que desta vez implementa a lição #9
  corretamente: idempotência checada pelo *resultado* (`class
  VocalProfile` já existe no arquivo?), validação de todas as âncoras
  antes de qualquer escrita (tudo ou nada), sem auto-commit. Testado 2x
  em sandbox antes de chegar ao usuário (1ª aplica, 2ª detecta e não
  duplica) e rodado de verdade no repo: **122 passed**.

## Pendência imediata — falta só isso pra fechar o ciclo

```bash
cd ~/MELO
git diff -- packages/catalog/store.py   # revisar antes de confiar
git add packages/catalog/store.py
git commit -m "feat(catalog): vocal_profiles + digital_twins (perfis vocais estruturados e gêmeos digitais licenciados)"
git push origin main
```

## Pendências antigas, ainda não resolvidas por nenhuma sessão

- 4 arquivos untracked de sessão anterior sem decisão: `send_to_colab.sh`,
  `fetch_from_colab.sh`, `populate_tracks.py`,
  `scripts/detect_track_boundaries.py` — revisados, tecnicamente seguros,
  só falta `git add` explícito se for pra manter.
- `cleanup_dev_scripts.sh` / `reorganize_scripts.sh`: seguem sem leitura.
- Fingerprinting de faixa em repertório de nicho: só 1 teste real (AudD),
  não reconheceu — inconclusivo.
- `packages/voices/generator.py`: interface pronta
  (`InstrumentalAdapter` funcional, `VoiceGenerator` exige backend), zero
  backend de voz real plugado. Segue sendo o gargalo central do produto.
- Validação com 1 titular de catálogo real: não feita, bloqueador citado
  em múltiplas sessões.
- `full_mix_analysis.py` merece um ajuste de dois pontos, não feito ainda:
  (1) trocar default de `--modelo tiny` para `small`; (2) adicionar
  checkpoint incremental (grava a cada segmento, não só no final) — usar
  o padrão de `scripts/transcribe_segments_overnight.py` (não usado nesta
  sessão, mas escrito e testado logicamente) como referência.

## Nota de disciplina que se manteve firme a sessão inteira

Toda vez que um arquivo já existente precisou ser lido antes de editar,
foi pedido `cat` real em vez de confiar em memória — e isso continuou
prevenindo erro (a réplica exata do `store.py` real, usada pra testar
`add_vocal_profiles.py` antes de entregar, só foi possível porque o
conteúdo real tinha sido colado nesta conversa). Continue assim.
