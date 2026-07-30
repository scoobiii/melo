#!/bin/bash
# -----------------------------------------------------------------------------
# integrate_metadata.sh
# Integra metadados de contato do DJ (Instagram, SoundCloud, download) no sistema.
# Uso: ./scripts/integrate_metadata.sh
# -----------------------------------------------------------------------------
set -e

cd "$(dirname "$0")/.."

echo "🔗 Integrando metadados do DJ..."
echo "================================"

# 1. Executar script de adição de metadados (se não executado ainda)
if ! sqlite3 melo_catalog.db "SELECT instagram FROM mixes LIMIT 1;" | grep -q "@"; then
    echo "📝 Adicionando metadados ao SQLite..."
    python3 scripts/add_mix_metadata.py
else
    echo "✅ Metadados já existem no SQLite."
fi

# 2. Adicionar endpoint /api/mix ao server.py (se não existir)
if ! grep -q "/api/mix" server.py; then
    echo "📄 Adicionando endpoint /api/mix ao server.py..."
    # Inserir antes do último `if __name__ == "__main__":`
    sed -i '/^if __name__ == "__main__":/i \
@app.route("/api/mix")\
def get_mix():\
    conn = sqlite3.connect("melo_catalog.db")\
    cursor = conn.cursor()\
    cursor.execute("SELECT id, instagram, soundcloud, download_link, call_to_action FROM mixes WHERE id = 1")\
    row = cursor.fetchone()\
    conn.close()\
    if row:\
        return jsonify({\
            "id": row[0],\
            "instagram": row[1] or "",\
            "soundcloud": row[2] or "",\
            "download_link": row[3] or "",\
            "call_to_action": row[4] or ""\
        })\
    return jsonify({"error": "Mix not found"}), 404
' server.py
    echo "✅ Endpoint /api/mix adicionado."
else
    echo "✅ Endpoint /api/mix já existe."
fi

# 3. Atualizar o player (static/index.html) com rodapé de metadados
if ! grep -q "footer-metadata" static/index.html; then
    echo "📄 Adicionando rodapé com metadados ao player..."
    # Inserir antes do fechamento do </body>
    sed -i '/<\/body>/i \
  <div class="footer-metadata" style="padding: 10px 16px; background: #0d0d13; border-top: 1px solid #1e1e2a; text-align: center; font-size: 12px; color: #888;">\
    <span id="metadata-placeholder">Carregando...</span>\
  </div>\
  <script>\
    async function loadMetadata() {\
      try {\
        const res = await fetch("/api/mix");\
        if (!res.ok) throw new Error("Falha ao carregar metadados");\
        const data = await res.json();\
        const el = document.getElementById("metadata-placeholder");\
        if (data.call_to_action) el.innerHTML = `<strong>${data.call_to_action}</strong> &bull; `;\
        if (data.instagram) el.innerHTML += `<a href="https://www.instagram.com/${data.instagram.replace("@","")}" target="_blank" style="color: #ff8a5c;">📸 ${data.instagram}</a>`;\
        if (data.soundcloud) el.innerHTML += ` &bull; <a href="${data.soundcloud}" target="_blank" style="color: #ff8a5c;">🎧 SoundCloud</a>`;\
        if (data.download_link) el.innerHTML += ` &bull; <a href="${data.download_link}" target="_blank" style="color: #ff8a5c;">📥 Download</a>`;\
      } catch (err) {\
        document.getElementById("metadata-placeholder").textContent = "❌ Metadados não disponíveis";\
      }\
    }\
    loadMetadata();\
  </script>
' static/index.html
    echo "✅ Rodapé adicionado ao player."
else
    echo "✅ Rodapé já existe no player."
fi

# 4. Reiniciar o servidor (se estiver rodando)
if pgrep -f "server.py" > /dev/null || pgrep -f "waitress-serve" > /dev/null; then
    echo "🔄 Reiniciando servidor..."
    pkill -f "server.py" 2>/dev/null || true
    pkill -f "waitress-serve" 2>/dev/null || true
    sleep 1
    ./scripts/deploy_player.sh -p 5000 &
    echo "✅ Servidor reiniciado."
else
    echo "🚀 Servidor não está rodando. Inicie com ./scripts/deploy_player.sh -p 5000"
fi

echo "================================"
echo "✅ Integração concluída!"
echo "   Acesse http://localhost:5000 para ver os metadados no rodapé."
