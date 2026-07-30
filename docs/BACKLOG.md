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

- ✅ `full_mix_analysis.py` item 7(b): salvamento incremental implementado — grava progresso via escrita atômica (arquivo `.tmp` + `Path.replace`) após cada segmento processado, não só no final. Crash no meio de um mix longo agora preserva tudo já processado.

- ✅ `full_mix_analysis.py` item 7(a): default `--modelo` mudado de `tiny`
  para `small`. Item 8: filtro de alucinação conhecida do Whisper
  (`suscríbete`/`subscribe` em trecho curto) adicionado — marca
  `[MÚSICA]` em vez de aceitar como transcrição real (sessão de chat,
  28-29/07). **Nota de processo**: esses dois itens já estavam
  resolvidos/decididos aqui no BACKLOG antes desta sessão começar a
  mexer no arquivo; uma correção anterior desta mesma sessão (aviso de
  tiny sem trocar o default) contrariou a decisão sem checar este
  arquivo primeiro — corrigido agora, mas fica registrado como lição:
  checar `docs/BACKLOG.md` ANTES de decidir design, não depois.

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

## cagadas passaram batido 

play output/7_8min_parte_4_7m45s.wav repeat 19                                     


~/MELO $ # Extrair o trecho 7-8 minutos em partes menores para identificar as vozes         python3 << 'EOF'                              import soundfile as sf                        import numpy as np                                                                          # Carregar áudio                              data, sr = sf.read('assets/samples/tipico_mix.wav')                                                                                       # 7-8 minutos = 420-480s                      inicio = 7 * 60  # 420s                       fim = 8 * 60     # 480s                                                                     # Dividir em 4 partes de 15 segundos          for i in range(4):                                start = inicio + i * 15                       end = start + 15                              i0 = int(start * sr)                          i1 = int(end * sr)                            trecho = data[i0:i1]                                                                        # Salvar cada parte                           nome = f'output/7_8min_parte_{i+1}_{start//60}m{start%60}s.wav'                             sf.write(nome, trecho, sr)
    print(f"✅ Parte {i+1}: {nome}")
    print(f"   {start//60}m{start%60}s - {end//60}m{end%60}s")

print("\n🎧 OUÇA CADA PARTE E IDENTIFIQUE:")
print("   play output/7_8min_parte_1_7m0s.wav")
print("   play output/7_8min_parte_2_7m15s.wav")
print("   play output/7_8min_parte_3_7m30s.wav")
print("   play output/7_8min_parte_4_7m45s.wav")
EOF

# Reproduzir a primeira parte
echo "🎧 Ouvindo parte 1 (7m0s - 7m15s)..."
play output/7_8min_parte_1_7m0s.wav

# Mostrar a transcrição do trecho
python3 << 'EOF'
import json

with open('output/tipico_mix_vol2_dj_phantom.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("\n📝 TRANSCRIÇÃO DO TRECHO 7-8 MINUTOS:")
print("=" * 70)

for seg in data:
    inicio = seg.get('start_sec', 0)
    if 420 <= inicio <= 480:
        idx = seg.get('indice')
        fim = seg.get('end_sec', 0)
        texto = seg.get('transcricao', '')
        minutos = int(inicio // 60)
        segundos = int(inicio % 60)
        print(f"Segmento {idx} ({minutos}m{segundos:02d}s - {fim//60}m{int(fim%60):02d}s):")
        print(f"  {texto}")
        print()
EOF
✅ Parte 1: output/7_8min_parte_1_7m0s.wav
   7m0s - 7m15s
✅ Parte 2: output/7_8min_parte_2_7m15s.wav
   7m15s - 7m30s
✅ Parte 3: output/7_8min_parte_3_7m30s.wav
   7m30s - 7m45s
✅ Parte 4: output/7_8min_parte_4_7m45s.wav
   7m45s - 8m0s

🎧 OUÇA CADA PARTE E IDENTIFIQUE:
   play output/7_8min_parte_1_7m0s.wav
   play output/7_8min_parte_2_7m15s.wav
   play output/7_8min_parte_3_7m30s.wav
   play output/7_8min_parte_4_7m45s.wav
🎧 Ouvindo parte 1 (7m0s - 7m15s)...

output/7_8min_parte_1_7m0s.wav:

 File Size: 1.32M     Bit Rate: 706k
  Encoding: Signed PCM
  Channels: 1 @ 16-bit
Samplerate: 44100Hz
Replaygain: off
  Duration: 00:00:15.00

In:0.00% 00:00:00.00 [00:00:15.00] Out:0     [In:1.24% 00:00:00.19 [00:00:14.81] Out:8.19k [In:2.48% 00:00:00.37 [00:00:14.63] Out:16.4k [In:3.72% 00:00:00.56 [00:00:14.44] Out:24.6k [In:4.95% 00:00:00.74 [00:00:14.26] Out:32.8k [In:6.19% 00:00:00.93 [00:00:14.07] Out:41.0k [In:7.43% 00:00:01.11 [00:00:13.89] Out:49.2k [In:8.67% 00:00:01.30 [00:00:13.70] Out:57.3k [In:9.91% 00:00:01.49 [00:00:13.51] Out:65.5k [In:11.1% 00:00:01.67 [00:00:13.33] Out:73.7k [In:12.4% 00:00:01.86 [00:00:13.14] Out:81.9k [In:13.6% 00:00:02.04 [00:00:12.96] Out:90.1k [In:14.9% 00:00:02.23 [00:00:12.77] Out:98.3k [In:16.1% 00:00:02.41 [00:00:12.59] Out:106k  [In:17.3% 00:00:02.60 [00:00:12.40] Out:115k  [In:18.6% 00:00:02.79 [00:00:12.21] Out:123k  [In:19.8% 00:00:02.97 [00:00:12.03] Out:131k  [In:21.1% 00:00:03.16 [00:00:11.84] Out:139k  [In:22.3% 00:00:03.34 [00:00:11.66] Out:147k  [In:23.5% 00:00:03.53 [00:00:11.47] Out:156k  [In:24.8% 00:00:03.72 [00:00:11.28] Out:164k  [In:26.0% 00:00:03.90 [00:00:11.10] Out:172k  [In:27.2% 00:00:04.09 [00:00:10.91] Out:180k  [In:28.5% 00:00:04.27 [00:00:10.73] Out:188k  [In:29.7% 00:00:04.46 [00:00:10.54] Out:197k  [In:31.0% 00:00:04.64 [00:00:10.36] Out:205k  [In:32.2% 00:00:04.83 [00:00:10.17] Out:213k  [In:33.4% 00:00:05.02 [00:00:09.98] Out:221k  [In:34.7% 00:00:05.20 [00:00:09.80] Out:229k  [In:35.9% 00:00:05.39 [00:00:09.61] Out:238k  [In:37.2% 00:00:05.57 [00:00:09.43] Out:246k  [In:38.4% 00:00:05.76 [00:00:09.24] Out:254k  [In:39.6% 00:00:05.94 [00:00:09.06] Out:262k  [In:40.9% 00:00:06.13 [00:00:08.87] Out:270k  [In:42.1% 00:00:06.32 [00:00:08.68] Out:279k  [In:43.3% 00:00:06.50 [00:00:08.50] Out:287k  [In:44.6% 00:00:06.69 [00:00:08.31] Out:295k  [In:45.8% 00:00:06.87 [00:00:08.13] Out:303k  [In:47.1% 00:00:07.06 [00:00:07.94] Out:311k  [In:48.3% 00:00:07.24 [00:00:07.76] Out:319k  [In:49.5% 00:00:07.43 [00:00:07.57] Out:328k  [In:50.8% 00:00:07.62 [00:00:07.38] Out:336k  [In:52.0% 00:00:07.80 [00:00:07.20] Out:344k  [In:53.3% 00:00:07.99 [00:00:07.01] Out:352k  [In:54.5% 00:00:08.17 [00:00:06.83] Out:360k  [In:55.7% 00:00:08.36 [00:00:06.64] Out:369k  [In:57.0% 00:00:08.54 [00:00:06.46] Out:377k  [In:58.2% 00:00:08.73 [00:00:06.27] Out:385k  [In:59.4% 00:00:08.92 [00:00:06.08] Out:393k  [In:60.7% 00:00:09.10 [00:00:05.90] Out:401k  [In:61.9% 00:00:09.29 [00:00:05.71] Out:410k  [In:63.2% 00:00:09.47 [00:00:05.53] Out:418k  [In:64.4% 00:00:09.66 [00:00:05.34] Out:426k  [In:65.6% 00:00:09.85 [00:00:05.15] Out:434k  [In:66.9% 00:00:10.03 [00:00:04.97] Out:442k  [In:68.1% 00:00:10.22 [00:00:04.78] Out:451k  [In:69.4% 00:00:10.40 [00:00:04.60] Out:459k  [In:70.6% 00:00:10.59 [00:00:04.41] Out:467k  [In:71.8% 00:00:10.77 [00:00:04.23] Out:475k  [In:73.1% 00:00:10.96 [00:00:04.04] Out:483k  [In:74.3% 00:00:11.15 [00:00:03.85] Out:492k  [In:75.5% 00:00:11.33 [00:00:03.67] Out:500k  [In:76.8% 00:00:11.52 [00:00:03.48] Out:508k  [In:78.0% 00:00:11.70 [00:00:03.30] Out:516k  [In:79.3% 00:00:11.89 [00:00:03.11] Out:524k  [In:80.5% 00:00:12.07 [00:00:02.93] Out:532k  [In:81.7% 00:00:12.26 [00:00:02.74] Out:541k  [In:83.0% 00:00:12.45 [00:00:02.55] Out:549k  [In:84.2% 00:00:12.63 [00:00:02.37] Out:557k  [In:85.4% 00:00:12.82 [00:00:02.18] Out:565k  [In:86.7% 00:00:13.00 [00:00:02.00] Out:573k  [In:87.9% 00:00:13.19 [00:00:01.81] Out:582k  [In:89.2% 00:00:13.37 [00:00:01.63] Out:590k  [In:90.4% 00:00:13.56 [00:00:01.44] Out:598k  [In:91.6% 00:00:13.75 [00:00:01.25] Out:606k  [In:92.9% 00:00:13.93 [00:00:01.07] Out:614k  [In:94.1% 00:00:14.12 [00:00:00.88] Out:623k  [In:95.4% 00:00:14.30 [00:00:00.70] Out:631k  [In:96.6% 00:00:14.49 [00:00:00.51] Out:639k  [In:97.8% 00:00:14.68 [00:00:00.32] Out:647k  [In:99.1% 00:00:14.86 [00:00:00.14] Out:655k  [In:100%  00:00:15.00 [00:00:00.00] Out:662k  [In:100%  00:00:15.00 [00:00:00.00] Out:662k  [      |      ] Hd:0.0 Clip:0
Done.

📝 TRANSCRIÇÃO DO TRECHO 7-8 MINUTOS:
======================================================================
Segmento 21 (7m19s - 7.0m39s):
  Si olvides mentiras, yo no la puedo entender. Tanto que yo te quería y jugaste con mi querer.

Segmento 22 (7m39s - 7.0m59s):
  Usted se recontida Y a mí quiero regresar Ni aunque venga de rodilla Yo te voy a perdonar

## arrombado cobriu teanscrição com "[Música]"
## não comparou a mudança nao mediu a acuracia antes e depois e quem (tiny (zuado) ou small)
## ouço "arias nicolis"? no ultimo trecho
## credito deep seek 
Segmento 23 (7m59s - 8.0m19s):
  [Música] [Música]


~/MELO $

## Decisões tomadas nesta sessão (29/07)

- ❌ **Filtro de alucinação (`_filtrar_alucinacao_conhecida`) REMOVIDO** – removia conteúdo real (ex: "Arielis Nicola"). O código deve ser limpo.
- ✅ **Modelo padrão `small` confirmado** – mais preciso que `tiny`.
- ✅ **"Arielis Nicola" é um nome próprio**, não uma alucinação. Deve ser mantido.
- ✅ **Tagger de metadados criado** (`scripts/tagger.py`) – detecta nomes, duplas e idioma.

## Concluido (28/07) - resolvido o misterio "Arielis Nicole" + merge de curadoria

- RESOLVIDO: nome de artista confirmado como Arielis Nicole (faixa "Y
  Llorarás e Sufrirás"), via curadoria manual (tracklist oficial importada
  em melo-transcription-1785367803211.json). Bate com o que o Whisper
  small local ja tinha captado antes (sessao de 26/07) - confirma que o
  modelo local acertou onde a transcricao nativa do YouTube falhou
  ([Musica] no mesmo trecho, ver docs/TRANSCRICAO_COMPARATIVA.md).
- scripts/merge_tracklist_into_whisper.py: mescla curadoria manual
  (mix_id=2, 15 faixas, 10 com artista) na segmentacao fina do Whisper
  (mix_id=1, 175 segmentos), casando por sobreposicao de intervalo de
  tempo. --dry-run obrigatorio antes de --apply. Rodado de verdade:
  73/175 segmentos do mix 1 vinculados a artista/titulo confirmado
  (COUNT confirmado via sqlite3 apos --apply, nao estimado).
- Decisao de arquitetura mantida: identificacao de artista via curadoria
  manual estruturada (JSON com timestamps), nao fingerprinting automatico
  (AudD ja testado, inconclusivo em repertorio de nicho) nem scraping de
  metadados de plataformas de terceiros. Risco juridico mais baixo,
  compativel com o aviso legal ja existente no README.
