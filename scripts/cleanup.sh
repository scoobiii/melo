#!/bin/bash
# Limpeza de arquivos desnecessários antes do commit

echo "🧹 Limpando lixo do MELO..."

# 1. Remover backups
find . -name "*.bak" -type f -delete
find . -name "*.tmp" -type f -delete

# 2. Remover caches Python
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null
find . -name ".pytest_cache" -type d -exec rm -rf {} + 2>/dev/null
find . -name ".mypy_cache" -type d -exec rm -rf {} + 2>/dev/null

# 3. Remover scripts de sessão antigos (que não são mais necessários)
rm -f check_segments_7_8.py
rm -f reconcile_backlog_7_8.sh
rm -f fix_model_tracking.sh
rm -f incremental_save.sh
rm -f remove_filter_forreal.sh

# 4. Remover logs
rm -f server.log
rm -f output/watchdog.log

# 5. Limpar output/ (se estiver no .gitignore, não precisa)
# rm -rf output/*  # cuidado: não remover se tiver arquivos importantes

echo "✅ Limpeza concluída."
echo ""
echo "📋 Arquivos para commitar (adicione manualmente):"
git status --short
