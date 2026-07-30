#!/usr/bin/env python3
"""
Gera player HTML com YouTube embed + transcrição sincronizada.
Uso: python scripts/transcript_player_yt.py --json output.json --video-id VIDEO_ID --out player.html
"""
import json
import argparse
from pathlib import Path

HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<title>MELO — Player com Transcrição</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  html, body { height: 100%; background: #0a0a0f; font-family: -apple-system, system-ui, sans-serif; }
  .layout { display: flex; flex-direction: column; height: 100vh; width: 100vw; }
  .video-pane {
    flex: 1 1 50%;
    position: relative;
    background: #000;
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
  }
  .video-pane iframe { width: 100%; height: 100%; border: 0; }
  .transcript-pane {
    flex: 1 1 50%;
    background: linear-gradient(180deg, #12121a, #0a0a0f);
    display: flex;
    flex-direction: column;
    border-top: 2px solid #2a2a3a;
  }
  .transcript-header {
    padding: 10px 16px;
    font-size: 12px;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #7a7a95;
    border-bottom: 1px solid #1e1e2a;
    display: flex;
    justify-content: space-between;
  }
  .transcript-header .badge { color: #ff8a5c; font-weight: 600; }
  .transcript-scroll {
    flex: 1;
    overflow-y: auto;
    padding: 24px 20px;
    scroll-behavior: smooth;
  }
  .line {
    color: #4a4a5e;
    font-size: 17px;
    line-height: 1.7;
    padding: 6px 0;
    transition: color 0.25s ease, transform 0.25s ease;
    cursor: pointer;
  }
  .line:hover { color: #9a9ab0; }
  .line.active {
    color: #fff;
    font-weight: 600;
    transform: scale(1.02);
  }
  .line .ts {
    display: inline-block;
    width: 46px;
    color: #555;
    font-size: 12px;
    font-family: monospace;
    margin-right: 10px;
  }
  .line.active .ts { color: #ff8a5c; }
  .note {
    padding: 8px 16px;
    font-size: 11px;
    color: #555;
    border-top: 1px solid #1e1e2a;
    background: #0d0d13;
  }
</style>
</head>
<body>
<div class="layout">
  <div class="video-pane">
    <iframe
      id="ytplayer"
      src="https://www.youtube.com/embed/{{VIDEO_ID}}?enablejsapi=1&rel=0"
      title="YouTube video player"
      frameborder="0"
      allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
      allowfullscreen>
    </iframe>
  </div>
  <div class="transcript-pane">
    <div class="transcript-header">
      <span>Transcrição — MELO (whisper.cpp local)</span>
      <span class="badge">● live sync</span>
    </div>
    <div class="transcript-scroll" id="scrollArea"></div>
    <div class="note">Clique em uma linha para pular o vídeo para o timestamp.</div>
  </div>
</div>

<script>
const transcriptData = {{TRANSCRIPT_DATA}};

const scrollArea = document.getElementById('scrollArea');
transcriptData.forEach((seg, i) => {
  const div = document.createElement('div');
  div.className = 'line';
  div.dataset.index = i;
  div.dataset.start = seg.start;
  const m = Math.floor(seg.start / 60);
  const s = String(seg.start % 60).padStart(2, '0');
  div.innerHTML = `<span class="ts">${m}:${s}</span>${seg.text}`;
  div.addEventListener('click', () => seekTo(seg.start));
  scrollArea.appendChild(div);
});

let player;
function onYouTubeIframeAPIReady() {
  player = new YT.Player('ytplayer', {
    events: { onReady: startSyncLoop }
  });
}

function seekTo(seconds) {
  if (player && player.seekTo) player.seekTo(seconds, true);
}

function startSyncLoop() {
  setInterval(() => {
    if (!player || !player.getCurrentTime) return;
    const t = player.getCurrentTime();
    let activeIndex = 0;
    transcriptData.forEach((seg, i) => { if (t >= seg.start) activeIndex = i; });

    document.querySelectorAll('.line').forEach((el, i) => {
      el.classList.toggle('active', i === activeIndex);
    });
    const activeEl = document.querySelector(`.line[data-index="${activeIndex}"]`);
    if (activeEl) activeEl.scrollIntoView({ block: 'center', behavior: 'smooth' });
  }, 500);
}

const tag = document.createElement('script');
tag.src = "https://www.youtube.com/iframe_api";
document.body.appendChild(tag);
</script>
</body>
</html>
'''

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", required=True, help="JSON do full_mix_analysis.py")
    parser.add_argument("--video-id", required=True, help="ID do vídeo do YouTube")
    parser.add_argument("--out", default="player_yt.html", help="Arquivo HTML de saída")
    args = parser.parse_args()

    with open(args.json, 'r', encoding='utf-8') as f:
        data = json.load(f)

    segments = data if isinstance(data, list) else data.get("segments", [])

    # Montar dados para JavaScript
    js_data = []
    for seg in segments:
        start = seg.get("start_sec", 0)
        text = seg.get("transcricao", "").replace('"', '\\"').replace("\n", " ")
        js_data.append(f'{{ start: {start}, text: "{text}" }}')

    transcript_js = "[" + ",".join(js_data) + "]"

    html = HTML_TEMPLATE.replace("{{VIDEO_ID}}", args.video_id)
    html = html.replace("{{TRANSCRIPT_DATA}}", transcript_js)

    out_path = Path(args.out)
    out_path.write_text(html, encoding="utf-8")
    print(f"✅ Player gerado: {out_path}")
    print(f"   {len(segments)} segmentos carregados")
    print(f"   Vídeo ID: {args.video_id}")

if __name__ == "__main__":
    main()
