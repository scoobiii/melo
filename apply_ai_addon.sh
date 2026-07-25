#!/usr/bin/env bash
# Localização no repo: apply_ai_addon.sh (raiz do projeto, ao lado de
# fix_repo_layout.sh e dos outros patch_*.sh)
#
# Aplica o addon packages/prompts + packages/ai + testes + CI dentro da
# árvore real do MELO. Idempotente: pode rodar mais de uma vez.
#
# Uso:
#   ./apply_ai_addon.sh /caminho/para/melo_addon
#
# Se nenhum argumento for passado, assume que este script está sendo
# executado de dentro da pasta melo_addon/ extraída.

set -euo pipefail

ADDON_SRC="${1:-$(dirname "$0")}"
REPO_ROOT="$(pwd)"

if [[ ! -d "$ADDON_SRC/packages" ]]; then
  echo "Erro: '$ADDON_SRC' não parece ser a pasta melo_addon (sem packages/)." >&2
  echo "Uso: ./apply_ai_addon.sh /caminho/para/melo_addon" >&2
  exit 1
fi

if [[ ! -f "$REPO_ROOT/README.md" ]]; then
  echo "Aviso: não encontrei README.md em $REPO_ROOT — confirme que você" >&2
  echo "está rodando este script na raiz do repo MELO." >&2
fi

echo "==> Copiando packages/prompts"
mkdir -p "$REPO_ROOT/packages/prompts"
cp "$ADDON_SRC/packages/prompts/__init__.py" "$REPO_ROOT/packages/prompts/__init__.py"
cp "$ADDON_SRC/packages/prompts/templates.py" "$REPO_ROOT/packages/prompts/templates.py"

echo "==> Copiando packages/ai"
mkdir -p "$REPO_ROOT/packages/ai"
cp "$ADDON_SRC/packages/ai/__init__.py" "$REPO_ROOT/packages/ai/__init__.py"
cp "$ADDON_SRC/packages/ai/adapter.py" "$REPO_ROOT/packages/ai/adapter.py"

echo "==> Copiando testes"
mkdir -p "$REPO_ROOT/tests/unit"
cp "$ADDON_SRC/tests/unit/test_ai_adapter.py" "$REPO_ROOT/tests/unit/test_ai_adapter.py"

echo "==> Copiando CI"
mkdir -p "$REPO_ROOT/.github/workflows"
cp "$ADDON_SRC/.github/workflows/ci.yml" "$REPO_ROOT/.github/workflows/ci.yml"

echo "==> Atualizando requirements/ai.txt"
mkdir -p "$REPO_ROOT/requirements"
if ! grep -q "^anthropic" "$REPO_ROOT/requirements/ai.txt" 2>/dev/null; then
  echo "anthropic>=0.40.0" >> "$REPO_ROOT/requirements/ai.txt"
  echo "    adicionada linha 'anthropic>=0.40.0'"
else
  echo "    já presente, nada a fazer"
fi

echo ""
echo "==> Arquivos aplicados. Próximos passos sugeridos:"
echo "    pip install -r requirements/ai.txt --break-system-packages"
echo "    pytest tests/unit/test_ai_adapter.py -v"
echo "    git add packages/prompts packages/ai tests/unit/test_ai_adapter.py .github/workflows/ci.yml requirements/ai.txt"
echo "    git commit -m 'feat: adapter de IA para adaptação de letra + CI pipeline'"
echo "    git push"
