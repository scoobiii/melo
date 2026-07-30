#!/bin/bash
# -----------------------------------------------------------------------------
# deploy_player.sh
# Transforma o player estático em dinâmico (consome API) e inicia o servidor.
# Uso: ./scripts/deploy_player.sh -p 5000 [-r]
# -----------------------------------------------------------------------------
set -e

cd "$(dirname "$0")/.."

PORT=5000
REBUILD=false

while getopts "p:r" opt; do
    case $opt in
        p) PORT=$OPTARG ;;
        r) REBUILD=true ;;
        *) echo "Uso: $0 -p PORTA [-r]" && exit 1 ;;
    esac
done

echo "🔧 MELO Player Deploy"
echo "======================"
echo "Porta: $PORT"
echo "Rebuild: $REBUILD"

# 1. Garantir que o SQLite existe
if [ ! -f "outputs/catalogo_validado.sqlite" ]; then
    echo "❌ SQLite não encontrado. Rode make catalog primeiro."
    exit 1
fi

# 2. Criar diretório static (se não existir)
mkdir -p static

# 3. Gerar o player dinâmico (ou copiar o existente se não for rebuild)
if [ "$REBUILD" = "true" ] || [ ! -f "static/index.html" ]; then
    echo "📄 Gerando player dinâmico (consome API)..."
    cat > static/index.html << 'HTML'
<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>MELO — Player Dinâmico</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  html, body { height: 100%; background: #0a0a0f; font-family: -apple-system, system-ui, sans-serif; }
  .layout { display: flex; flex-direction: column; height: 100vh; width: 100vw; }
  .video-pane { flex: 1 1 50%; background: #000; display: flex; align-items: center; justify-content: center; overflow: hidden; }
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
  .error { color: #f55; text-align: center; padding: 20px; }
  .loading { color: #888; text-align: center; padding: 20px; font-style: italic; }
</style>
</head>
<body>
<div class="layout">
  <div class="video-pane">
    <iframe id="ytplayer" src="https://www.youtube.com/embed/CoNANz87dTk?enablejsapi=1&rel=0" allowfullscreen></iframe>
  </div>
  <div class="transcript-pane">
    <div class="transcript-header"><span>Catálogo Validado — MELO</span><span class="badge" id="count">⏳</span></div>
    <div class="transcript-scroll" id="scrollArea"><div class="loading">Carregando...</div></div>
    <div class="note">Clique em uma linha para pular o vídeo. Dados da curadoria manual (SQLite).</div>
  </div>
</div>
<script>
const scrollArea = document.getElementById('scrollArea');
let player;

async function loadTracks() {
  try {
    const response = await fetch('/api/tracks');
    if (!response.ok) throw new Error('Falha ao carregar');
    const tracks = await response.json();
    document.getElementById('count').textContent = `${tracks.length} faixas`;
    scrollArea.innerHTML = '';
    tracks.forEach(track => {
      const div = document.createElement('div');
      div.className = 'line';
      div.dataset.start = track.start || 0;
      const m = Math.floor((track.start || 0) / 60);
      const s = String(Math.floor((track.start || 0) % 60)).padStart(2, '0');
      const artist = track.artist || '';
      const title = track.title || '';
      div.innerHTML = `<span class="ts">${m}:${s}</span><span class="artist">${artist}</span> — ${title}`;
      div.addEventListener('click', () => seekTo(parseFloat(track.start) || 0));
      scrollArea.appendChild(div);
    });
  } catch (err) {
    scrollArea.innerHTML = `<div class="error">❌ Erro: ${err.message}</div>`;
  }
}

function seekTo(seconds) {
  if (player && player.seekTo) player.seekTo(seconds, true);
}

function onYouTubeIframeAPIReady() {
  player = new YT.Player('ytplayer', {
    events: { onReady: startSyncLoop }
  });
}

function startSyncLoop() {
  setInterval(() => {
    if (!player || !player.getCurrentTime) return;
    const t = player.getCurrentTime();
    const lines = document.querySelectorAll('.line');
    let activeIndex = 0;
    lines.forEach((line, i) => {
      const start = parseFloat(line.dataset.start);
      if (t >= start) activeIndex = i;
    });
    lines.forEach((line, i) => line.classList.toggle('active', i === activeIndex));
    const activeEl = document.querySelector('.line.active');
    if (activeEl) activeEl.scrollIntoView({ block: 'center', behavior: 'smooth' });
  }, 500);
}

loadTracks();
const tag = document.createElement('script');
tag.src = 'https://www.youtube.com/iframe_api';
document.body.appendChild(tag);
</script>
</body>
</html>
HTML
    echo "✅ static/index.html gerado."
fi

# 4. Copiar áudio (se existir) para static/ (opcional, mas útil)
if [ -f "assets/samples/tipico_mix.mp3" ]; then
    cp "assets/samples/tipico_mix.mp3" "static/tipico_mix.mp3"
    echo "🎵 Áudio copiado para static/"
elif [ -f "assets/samples/tipico_mix.wav" ]; then
    cp "assets/samples/tipico_mix.wav" "static/tipico_mix.wav"
    echo "🎵 Áudio copiado para static/"
fi

# 5. Matar processo na porta (se existir)
if lsof -i :$PORT >/dev/null 2>&1; then
    echo "⚠️ Porta $PORT em uso. Tentando matar..."
    kill -9 $(lsof -t -i :$PORT) 2>/dev/null || true
    sleep 1
fi

# 6. Iniciar o servidor
echo "🚀 Iniciando servidor na porta $PORT..."
export FLASK_APP=server.py
if command -v waitress-serve &> /dev/null; then
    echo "   Usando Waitress (produção)"
    waitress-serve --host=0.0.0.0 --port="$PORT" server:app &
else
    echo "   Usando Flask (desenvolvimento)"
    python3 server.py &
fi

sleep 2
echo "✅ Servidor rodando em http://localhost:$PORT"
# Tentar obter IP de forma portável
IP=$(ip -4 addr show | grep -oP '(?<=inet\s)\d+(\.\d+){3}' | grep -v 127.0.0.1 | head -1)
if [ -n "$IP" ]; then
    echo "   Acesse no celular: http://$IP:$PORT"
else
    echo "   (use ifconfig para descobrir seu IP e acessar)"
fi
echo "   (ou use ngrok para expor publicamente)"
