# Analise de Mix Completo - MELO

`scripts/full_mix_analysis.py` processa um mix de audio longo (ex: DJ mix
de 60+ min com multiplos artistas) de ponta a ponta:

1. Segmenta por mudanca de BPM/timbre (`packages/adaptation/mix_segmentation.py`)
2. Transcreve cada segmento localmente (`packages/lyrics/transcriber_cpp.py`,
   whisper.cpp - sem depender de API externa)
3. Produz um JSON com um registro por segmento: fronteiras absolutas, BPM,
   transcricao, e campos vazios (`artist`, `work`, `label`, `beneficiary`,
   `royalty_pct`) prontos para preenchimento.

## O que este script NAO faz

Nao identifica artista/obra automaticamente. Isso e decisao de negocio em
aberto - ver `docs/GAPS_NEGOCIO.md`. As pistas (`transcricao`, nomes
proprios cantados) servem para busca manual (Shazam, busca de letra) ou
integracao futura de fingerprinting (AudD/ACRCloud), nao implementada.

## Uso

```bash
# 1) converter o mix original para WAV (MP3 nao e lido diretamente - ver
#    docs/USER_GUIDE.md#formatos-de-audio)
ffmpeg -i mix_original.mp3 -ar 16000 -ac 1 mix.wav

# 2) rodar a analise completa
python scripts/full_mix_analysis.py mix.wav \
  --out output/mix_analise.json \
  --modelo tiny --idioma es --min-seg-sec 20 --max-segments 200
```

`--modelo tiny` e recomendado para arquivos longos (varredura rapida);
`small`/`medium` dao mais qualidade de transcricao mas sao
significativamente mais lentos em CPU de telefone.

## Proximo passo apos rodar

Editar o JSON de saida preenchendo `artist`, `work`, `label`,
`beneficiary`, `royalty_pct` por segmento, depois alimentar
`packages/catalog` (via `partners.py`) e calcular o split real com
`packages/publisher/royalties.py`.
