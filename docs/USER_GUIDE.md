# Guia do Usuário — MELO

## O que o pipeline faz hoje

Dado um arquivo de áudio e um gênero de origem panamenho, o pipeline:

1. Lê metadados do áudio (duração, sample rate, canais)
2. Estima o BPM analisando uma **janela de ~40s no centro do arquivo**
   (não o arquivo inteiro — ver nota abaixo)
3. Rankeia gêneros brasileiros correlatos, combinando correlação explícita
   de tradição + família de textura + proximidade de BPM
4. (Opcional) Transcreve a letra via Whisper local

O resultado é salvo em `output/<nome>_pipeline.json`.

## Uso

```bash
python scripts/run_pipeline.py caminho/faixa.wav --genero tipico_panameno
```

Opções:
- `--genero` (obrigatório): `tipico_panameno` | `cumbia_panamena` | `tamborito`
- `--sem-transcricao`: pula a etapa de Whisper (mais rápido, não exige o pacote instalado)
- `--modelo`: tamanho do modelo Whisper (`tiny`/`base`/`small`/`medium`/`large`) — default `small`
- `--idioma`: idioma alvo da transcrição — default `pt`
- `--saida`: caminho customizado do `.json` de saída

## Formatos de áudio

O carregador (`packages/audio`, via `soundfile`/`libsndfile`) lê nativamente
**WAV, FLAC, OGG**. Ele **não decodifica MP3** de forma confiável em todos
os ambientes (depende de como `libsndfile` foi compilada). Se seu arquivo é
MP3, converta antes com `ffmpeg`:

```bash
ffmpeg -i faixa.mp3 -ar 44100 -ac 1 faixa.wav
```

## Por que o BPM usa só uma janela de 40s, não o arquivo inteiro

BPM não é um conceito estável sobre um arquivo longo com múltiplas faixas
(ex.: um mix/playlist de DJ). Analisar o arquivo inteiro produz picos de
autocorrelação sem significado musical real — na prática, isso foi
observado diretamente: um mix de 62 minutos analisado por inteiro deu um
BPM ~198 (implausível para o gênero); a mesma faixa, analisada numa janela
de 40s do centro, deu ~96 (dentro do esperado). Para arquivos com uma única
música, a janela central costuma ser representativa. Para mixes/playlists,
o ideal é segmentar por faixa antes (não implementado ainda).

## Fontes de áudio legítimas

Use apenas áudio que você tem o direito de usar:
- Gravações/composições próprias
- Faixas com licença mecânica/sync já negociada
- Amostras de bancos de áudio licenciados

**Nunca** use ferramentas de extração/download de plataformas de streaming
como fonte de dados de produto. Isso viola ToS das plataformas e direito
autoral, independentemente da intenção declarada (regravação, adaptação,
"uso educacional" etc.) — o pagamento posterior de royalty não retroage
para legalizar a extração não autorizada.

## Interpretando o output

```json
{
  "audio_path": "...",
  "duration_seconds": 3724.8,
  "bpm": 95.7,
  "genero_origem": "tipico_panameno",
  "correlacoes": [
    {"genero": "forro_pe_de_serra", "score": 0.929},
    {"genero": "vanerao", "score": 0.778}
  ],
  "transcricao": "...",
  "transcricao_erro": null
}
```

`score` das correlações é 0-1, combinando: presença na lista de correlação
explícita da tabela (peso 0.6) + mesma família de textura/instrumentação
(peso 0.2) + proximidade de BPM (peso 0.2). Não é uma medida musicológica
validada — é uma heurística de priorização, sujeita a revisão.
