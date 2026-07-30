


# MELO — Music Analysis Factory (não é "Adaptation" ainda)

**Estado atual:** protótipo funcional para análise de áudio e transcrição.  
**Não é produto.** Não gera áudio, não identifica artistas automaticamente, não tem distribuição.

---

## 🧪 O que realmente funciona (comprovado com áudio real)

- [x] Análise de áudio: duração, sample rate, BPM, RMS, centroide
- [x] Transcrição local com Whisper (modelo `small`, sem filtros)
- [x] Segmentação de mixes longos (início/fim de cada parte)
- [x] Detecção de autoapresentações (ex: "soy María", "Arielis Nicola")
- [x] Correlação de gêneros (Panamá ↔ Brasil) via BPM
- [x] SQLite para artistas, faixas, mixes, royalties
- [x] ~122 testes unitários (100% verdes)

---

## 🚫 O que NÃO funciona (e que o README antigo escondia)

- ❌ **Geração de áudio adaptado** – `VoiceGenerator` é só um esqueleto. Não há voz real.
- ❌ **Fingerprinting** – AudD não reconheceu repertório panamenho. Identificação é manual.
- ❌ **Source separation** – não existe separação vocal/instrumental (karaokê).
- ❌ **API** – tem endpoints, mas sem testes automatizados e sem Swagger/OpenAPI.
- ❌ **Salvamento incremental** – se o `full_mix_analysis.py` cair, perde tudo.
- ❌ **Metadados oficiais** (`artist`, `work`, `label`) – sempre vazios, só preenchidos manualmente.

---

## 🎯 O que o próximo GOS3 precisa fazer para virar produto

1. **Remover o filtro de alucinação** do código (já decidido, só não feito).
2. **Implementar salvamento incremental** no `full_mix_analysis.py`.
3. **Testar a API** (roteamento, erros, filtros).
4. **Decidir Swagger/OpenAPI** (ou documentação estática).
5. **Validar com um artista/catálogo real** – ação humana, não código.

---

## 🚀 Como usar (o que já funciona)

```bash
# 1. Converter MP3 para WAV (se necessário)
ffmpeg -i entrada.mp3 -ar 44100 -ac 1 -sample_fmt s16 saida.wav

# 2. Analisar o mix
python scripts/full_mix_analysis.py saida.wav --out resultado.json --modelo small

# 3. Executar testes
make test
```

---

⚠️ Aviso importante

Este projeto não inclui mecanismos de download de áudio de plataformas (YouTube, SoundCloud, etc.).
Todo áudio analisado deve ser de propriedade legítima do usuário.

---

Documentação completa: docs/
Backlog e decisões: docs/BACKLOG.md

```

---

## Fluxo atual do projeto

```
Áudio
  ↓ whisper.cpp (small)
Transcrição
  ↓ Curadoria manual (tracklist)
merge_tracklist_into_whisper.py
  ↓
validate_catalog.py (MusicBrainz)
  ↓
SQLite / JSON / CSV
```

### Comandos principais

```bash
make help
make install
make test
make catalog
```

O `validate_catalog.py` **não realiza fingerprinting**. Ele utiliza
artista/título previamente obtidos por transcrição e/ou curadoria manual
para validar e enriquecer metadados usando a API oficial do MusicBrainz.
