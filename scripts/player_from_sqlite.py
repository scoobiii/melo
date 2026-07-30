#!/usr/bin/env python3
"""
Gera player HTML usando os dados do SQLite do validador.
Uso: python scripts/player_from_sqlite.py --db outputs/catalogo_validado.sqlite --audio assets/samples/tipico_mix.wav --video-id CoNANz87dTk --out output/player_final.html
"""
import json
import sqlite3
import argparse
from pathlib import Path

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>MELO — Player com Catálogo Validado</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  html, body { height: 100%; background: #0a0a0f; font-family: -apple-system, system-ui, sans-serif; }
  .layout { display: flex; flex-direction: column; height: 100vh; width: 100vw; }
  .video-pane { flex: 1 1 50%; position: relative; background: #000; display: flex; align-items: center; justify-content: center; overflow: hidden; }
  .video-pane iframe { width: 100%; height: 100%; border: 0; }
  .transcript-pane { flex: 1 1 50%; background: #12121a; display: flex; flex-direction: column; border-top: 2px solid #2a2a3a; }
  .transcript-header { padding: 10px 16px; font-size: 12px; text-transform: uppercase; color: #7a7a95; border-bottom: 1px solid #1e1e2a; display: flex; justify-content: space-between; }
  .transcript-scroll { flex: 1; overflow-y: auto; padding: 24px 20px; scroll-behavior: smooth; }
  .line { color: #4a4a5e; font-size: 17px; line-height: 1.7; padding: 6px 0; transition: color 0.25s; cursor: pointer; }
  .line:hover { color: #9a9ab0; }
  .line.active { color: #fff; font-weight: 600; }
  .line .ts { display: inline-block; width: 46px; color: #555; font-size: 12px; font-family: monospace; margin-right: 10px; }
  .line .artist { color: #ff8a5c; font-weight: 400; }
  .line.active .ts { color: #ff8a5c; }
  .note { padding: 8px 16px; font-size: 11px; color: #555; border-top: 1px solid #1e1e2a; background: #0d0d13; }
</style>
</head>
<body>
<div class="layout">
  <div class="video-pane">
    <iframe id="ytplayer" src="https://www.youtube.com/embed/{{VIDEO_ID}}?enablejsapi=1&rel=0" allowfullscreen></iframe>
  </div>
  <div class="transcript-pane">
    <div class="transcript-header"><span>Catálogo Validado — MELO</span><span class="badge">● ${TOTAL} faixas</span></div>
    <div class="transcript-scroll" id="scrollArea"></div>
    <div class="note">Clique em uma linha para pular o vídeo.</div>
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
  const artist = seg.artist || '';
  div.innerHTML = `<span class="ts">${m}:${s}</span><span class="artist">${artist}</span> — ${seg.text}`;
  div.addEventListener('click', () => seekTo(seg.start));
  scrollArea.appendChild(div);
});
let player;
function onYouTubeIframeAPIReady() {
  player = new YT.Player('ytplayer', { events: { onReady: startSyncLoop } });
}
function seekTo(seconds) { if (player && player.seekTo) player.seekTo(seconds, true); }
function startSyncLoop() {
  setInterval(() => {
    if (!player || !player.getCurrentTime) return;
    const t = player.getCurrentTime();
    let activeIndex = 0;
    transcriptData.forEach((seg, i) => { if (t >= seg.start) activeIndex = i; });
    document.querySelectorAll('.line').forEach((el, i) => el.classList.toggle('active', i === activeIndex));
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
"""

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--db', required=True)
    parser.add_argument('--audio', required=True)
    parser.add_argument('--video-id', required=True)
    parser.add_argument('--out', default='output/player_final.html')
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT segment, start_time, matched_artist, matched_title
        FROM tracks
        ORDER BY segment
    """)
    rows = cursor.fetchall()
    conn.close()

    data = []
    for row in rows:
        seg, start, artist, title = row
        if not artist and not title:
            continue
        try:
            start_sec = float(start) if start else 0
        except:
            start_sec = 0
        data.append({
            'start': start_sec,
            'artist': artist or '',
            'text': title or ''
        })

    transcript_js = json.dumps(data)
    total = len(data)

    html = HTML_TEMPLATE.replace('{{VIDEO_ID}}', args.video_id)
    html = html.replace('${TOTAL}', str(total))
    html = html.replace('{{TRANSCRIPT_DATA}}', transcript_js)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding='utf-8')
    print(f"✅ Player gerado: {out_path} ({total} faixas)")

if __name__ == '__main__':
    main()
