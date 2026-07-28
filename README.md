# MELO — Music Adaptation Factory

Plataforma de análise, transcrição e adaptação musical entre gêneros regionais
(atualmente: raízes panamenhas — típico, cumbia, tamborito — correlacionadas
com gêneros brasileiros de tradição regional: forró, pisadinha, vanerão,
sertanejo).

## Status do projeto

**Estágio:** núcleo técnico funcional, validado com áudio real.

**O que funciona:**
- Análise de áudio (duração, sample rate, BPM, RMS, centroide)
- Transcrição de letras com Whisper (modelo small, sem filtros)
- Segmentação de mixes longos (identificação de faixas por início/fim)
- Detecção de autoapresentações (cantor/DJ)
- Correlação de gêneros (Panamá ↔ Brasil)
- Persistência em SQLite (artistas, faixas, mixes, royalties)
- Testes unitários (122+, 100% verdes)

**O que NÃO funciona (e não está no README):**
- Geração/regravação de áudio com voz real (VoiceGenerator é skeleton)
- Fingerprinting automático em repertório de nicho (AudD falhou)
- Source separation para karaokê (não existe)
- API com testes completos e Swagger (parcial)
- Salvamento incremental no `full_mix_analysis.py` (pendente)

Ver [ROADMAP.md](./ROADMAP.md) e [docs/BACKLOG.md](./docs/BACKLOG.md).
