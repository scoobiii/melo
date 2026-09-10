# MELO — Source Separation

## Objetivo

Transformar um mix musical em dois artefatos utilizáveis para karaokê:

- `*_VOCAL.wav`
- `*_INSTRUMENTAL.wav`

## Backend

O backend é Demucs. O MELO chama a API Python do pacote e usa o modo de duas fontes `--two-stems vocals`, cujo contrato produz `vocals` e `no_vocals`.

## CLI

```bash
PYTHONPATH=. python scripts/separate_vocals.py entrada.wav \
  --out output/separation \
  --model htdemucs \
  --device cpu \
  --segment 10 \
  --shifts 1
```

## API

```python
from packages.separation import separate_vocals_instrumental

result = separate_vocals_instrumental(
    "entrada.wav",
    "output/separation",
    model="htdemucs",
    device="cpu",
    segment=10,
    shifts=1,
)
```

## Recursos e restrições

`--segment` é o controle principal de memória. Em dispositivos com pouca RAM, comece com 10 segundos e aumente somente após validar estabilidade e qualidade.

`--shifts` é um ensemble de previsões. O valor 1 reduz custo; valores maiores podem melhorar a separação, mas aumentam tempo e memória.

A separação é estimativa de fonte, não remoção perfeita. Vazamento de voz, bleed instrumental e artefatos devem ser esperados e avaliados no arquivo final.

## Validação

O teste unitário mocka o backend e verifica:

1. validação de entrada;
2. validação de `segment` e `shifts`;
3. argumentos enviados ao Demucs;
4. descoberta dos stems;
5. publicação dos dois artefatos MELO.

A validação de qualidade de áudio deve ser feita com áudio real, porque testes unitários não medem SDR, bleed ou artefatos perceptuais.
