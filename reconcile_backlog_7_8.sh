#!/usr/bin/env bash
set -euo pipefail
TARGET="scripts/full_mix_analysis.py"
BACKLOG="docs/BACKLOG.md"

for f in "$TARGET" "$BACKLOG"; do
    [ -f "$f" ] || { echo "Não encontrado: $f — abortando."; exit 1; }
done

echo "==> MELO :: reconciliando BACKLOG item 7(a) e 8 (passaram batido na sessão anterior)"

python3 - "$TARGET" <<'PYEOF'
import sys
path = sys.argv[1]
src = open(path, encoding="utf-8").read()

# item 7(a): default tiny -> small (já decidido no BACKLOG, minha correção
# anterior contrariou isso sem querer)
replacements = [
    ('def analyze_mix(\n    wav_path: str,\n    min_seg_sec: float = 20.0,\n    max_segments: int = 200,\n    modelo: str = "tiny",',
     'def analyze_mix(\n    wav_path: str,\n    min_seg_sec: float = 20.0,\n    max_segments: int = 200,\n    modelo: str = "small",'),
    ('"--modelo", default="tiny",',
     '"--modelo", default="small",'),
]

missing = []
for old, new in replacements:
    if old in src:
        src = src.replace(old, new, 1)
    else:
        missing.append(old[:50])

if missing:
    print("Âncoras não encontradas (talvez já corrigido ou refatorado):", missing)
    sys.exit(1)

# item 8: filtro de alucinação óbvia do Whisper — marca transcrição que
# contém "suscríbete"/"subscribe" isolado (padrão conhecido de alucinação
# em trecho instrumental/silencioso) em vez de aceitar como texto real
old_texto = '''            try:
                texto = transcribe_audio(clip_path, modelo=modelo, idioma=idioma)
            except Exception as e:
                texto = f"[ERRO transcricao: {e}]"'''

new_texto = '''            try:
                texto = transcribe_audio(clip_path, modelo=modelo, idioma=idioma)
                texto = _filtrar_alucinacao_conhecida(texto)
            except Exception as e:
                texto = f"[ERRO transcricao: {e}]"'''

if old_texto not in src:
    print("Âncora do bloco de transcrição não encontrada — abortando.")
    sys.exit(1)
src = src.replace(old_texto, new_texto, 1)

# adiciona a função de filtro, antes de analyze_mix
anchor_def = "def analyze_mix("
filtro_func = '''_ALUCINACOES_CONHECIDAS = ("suscríbete", "suscribete", "subscribe", "like and subscribe")


def _filtrar_alucinacao_conhecida(texto: str) -> str:
    """Whisper tem alucinacao documentada em trechos instrumentais/silenciosos,
    tipicamente inserindo frases de call-to-action de video (ex: pedidos de
    inscricao em canal) que nao existem no audio real. Marca como [MUSICA]
    em vez de aceitar como transcricao real quando o texto e dominado por
    esses padroes conhecidos.
    """
    baixo = texto.lower().strip()
    if not baixo:
        return texto
    if any(padrao in baixo for padrao in _ALUCINACOES_CONHECIDAS):
        # se o texto e majoritariamente so a alucinacao (poucas palavras
        # alem do padrao conhecido), marca como instrumental
        palavras = baixo.split()
        if len(palavras) <= 6:
            return "[MÚSICA] (transcrição descartada: padrão de alucinação conhecido do Whisper)"
    return texto


'''
if anchor_def not in src:
    print("Âncora de analyze_mix não encontrada — abortando.")
    sys.exit(1)
src = src.replace(anchor_def, filtro_func + anchor_def, 1)

open(path, "w", encoding="utf-8").write(src)
print(f"==> {path}: default tiny->small, filtro de alucinação conhecida adicionado.")
PYEOF

echo "==> Rodando suíte completa..."
python -m pytest tests/ -q

echo "==> Atualizando docs/BACKLOG.md..."
python3 - "$BACKLOG" <<'PYEOF'
import sys
path = sys.argv[1]
src = open(path, encoding="utf-8").read()

old_item7 = '''7. **`full_mix_analysis.py`**: (a) default de `--modelo` é `tiny`, devia
   ser `small` (tiny é pior qualidade); (b) não salva progresso
   incrementalmente, só grava JSON no final — risco real se o processo
   cair no meio de um mix longo.
8. **Alucinação conhecida do Whisper** (`"¡Suscríbete!"` em trechos
   instrumentais/silêncio) sem filtro — sugestão já registrada: descartar
   ou marcar `[MÚSICA]` transcrição contendo `suscríbete`/`subscribe`.'''

new_item7 = '''7. **`full_mix_analysis.py` (b)**: não salva progresso incrementalmente,
   só grava JSON no final — risco real se o processo cair no meio de um
   mix longo. **Ainda pendente.**'''

if old_item7 in src:
    src = src.replace(old_item7, new_item7, 1)
else:
    print("Item 7/8 não encontrado no formato esperado — BACKLOG.md pode já ter mudado. Não editei.")
    sys.exit(1)

old_concluido = "## Concluído recentemente (não reabrir sem motivo novo)"
new_concluido = old_concluido + '''

- ✅ `full_mix_analysis.py` item 7(a): default `--modelo` mudado de `tiny`
  para `small`. Item 8: filtro de alucinação conhecida do Whisper
  (`suscríbete`/`subscribe` em trecho curto) adicionado — marca
  `[MÚSICA]` em vez de aceitar como transcrição real (sessão de chat,
  28-29/07). **Nota de processo**: esses dois itens já estavam
  resolvidos/decididos aqui no BACKLOG antes desta sessão começar a
  mexer no arquivo; uma correção anterior desta mesma sessão (aviso de
  tiny sem trocar o default) contrariou a decisão sem checar este
  arquivo primeiro — corrigido agora, mas fica registrado como lição:
  checar `docs/BACKLOG.md` ANTES de decidir design, não depois.'''

src = src.replace(old_concluido, new_concluido, 1)
open(path, "w", encoding="utf-8").write(src)
print(f"==> {path} atualizado.")
PYEOF

git add "$TARGET" "$BACKLOG"
git commit -m "fix(scripts): reconcilia BACKLOG itens 7(a) e 8 — default small, filtro de alucinação

Correção anterior desta sessão (12a43a1) tinha mantido --modelo tiny
como default só com aviso, sem checar docs/BACKLOG.md primeiro — esse
arquivo já registrava a decisão de trocar o default para small (tiny é
pior qualidade), tomada em sessão anterior. Revertido para o que já
estava decidido.

Item 8 do BACKLOG (alucinação conhecida do Whisper tipo
'¡Suscríbete!' em trecho instrumental/silencioso) também resolvido:
_filtrar_alucinacao_conhecida() marca [MÚSICA] em vez de aceitar como
transcrição real quando o texto é dominado por um padrão de call-to-action
de vídeo conhecido e tem poucas palavras além disso.

docs/BACKLOG.md atualizado: item 7(a) e 8 movidos para Concluído, com
nota de processo sobre checar o backlog antes de decidir design, não
depois."

git push origin main
git log -1 --oneline
