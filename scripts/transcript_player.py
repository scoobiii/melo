#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# Arquivo        : transcript_player.py
# Diretorio      : scripts/
# Responsabilidade:
#   Gera pagina HTML local com player de audio sincronizado a
#   transcricao (clica na linha, pula pro timestamp). Le o JSON de
#   full_mix_analysis.py, precisa do WAV correspondente. Ferramenta de
#   QA/revisao manual, nao faz parte do pipeline de producao.
# Versao         : 1.0.0
# Data/hora      : 2026-07-28
# Autoria        : MELO / GOS3 - Scrum . Agile . DevOps
# -----------------------------------------------------------------------------
"""
Uso:
    python scripts/transcript_player.py output/mix_analise.json audio.wav \
        --out output/player.html
    Depois abra output/player.html no navegador do celular.
"""
import argparse
import json
from pathlib import Path

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>MELO - Player de Transcricao</title>
<style>
  body { font-family: sans-serif; background: #111; color: #eee; margin: 0; padding: 0; }
  #player-bar { position: sticky; top: 0; background: #000; padding: 12px; z-index: 10; }
  audio { width: 100%; }
  #segments { padding: 8px; }
  .seg { padding: 10px 12px; margin: 4px 0; border-radius: 8px; cursor: pointer; background: #1a1a1a; }
  .seg:active, .seg.active { background: #2a3f5f; }
  .seg .time { color: #7ab; font-size: 0.85em; margin-right: 8px; }
  .seg .bpm { color: #888; font-size: 0.8em; float: right; }
  .seg .text { display: block; margin-top: 4px; }
  .seg .empty { color: #666; font-style: italic; }
</style>
</head>
<body>
<div id="player-bar">
  <audio id="audio" controls src="AUDIO_SRC_PLACEHOLDER"></audio>
</div>
<div id="segments">SEGMENTS_PLACEHOLDER</div>
<script>
const audio = document.getElementById('audio');
const segs = document.querySelectorAll('.seg');

segs.forEach(seg => {
  seg.addEventListener('click', () => {
    audio.currentTime = parseFloat(seg.dataset.start);
    audio.play();
  });
});

audio.addEventListener('timeupdate', () => {
  const t = audio.currentTime;
  let activeSeg = null;
  segs.forEach(seg => {
    const start = parseFloat(seg.dataset.start);
    const end = parseFloat(seg.dataset.end);
    if (t >= start && t < end) {
      activeSeg = seg;
    }
    seg.classList.remove('active');
  });
  if (activeSeg) {
    activeSeg.classList.add('active');
    activeSeg.scrollIntoView({block: 'center', behavior: 'smooth'});
  }
});
</script>
</body>
</html>
"""


def fmt_time(sec):
    m, s = divmod(int(sec), 60)
    return f"{m}:{s:02d}"


def build_segment_html(seg):
    start = seg.get("start_sec", 0)
    end = seg.get("end_sec", 0)
    bpm = seg.get("bpm")
    texto = seg.get("transcricao") or ""
    texto = texto.replace("<", "&lt;").replace(">", "&gt;")
    css_class = "text empty" if not texto.strip() or texto.strip() == "[MÚSICA]" else "text"
    bpm_str = f"bpm {bpm}" if bpm else ""
    return (
        f'<div class="seg" data-start="{start}" data-end="{end}">'
        f'<span class="time">{fmt_time(start)}-{fmt_time(end)}</span>'
        f'<span class="bpm">{bpm_str}</span>'
        f'<span class="{css_class}">{texto or "(sem transcricao)"}</span>'
        f'</div>'
    )


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("json_path", help="JSON de full_mix_analysis.py")
    ap.add_argument("audio_path", help="WAV correspondente")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    data = json.loads(Path(args.json_path).read_text(encoding="utf-8"))
    segments = data if isinstance(data, list) else data.get("segments", [])

    segments_html = "\n".join(build_segment_html(s) for s in segments)

    audio_path = Path(args.audio_path)
    out_path = Path(args.out)
    try:
        rel_audio = str(audio_path.resolve().relative_to(out_path.resolve().parent))
    except ValueError:
        rel_audio = str(audio_path.resolve())

    html = HTML_TEMPLATE.replace("AUDIO_SRC_PLACEHOLDER", rel_audio)
    html = html.replace("SEGMENTS_PLACEHOLDER", segments_html)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")

    print(f"==> {len(segments)} segmentos")
    print(f"==> Gerado: {out_path}")
    print(f"==> Abra no navegador do celular")


if __name__ == "__main__":
    main()
