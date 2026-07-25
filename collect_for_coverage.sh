#!/usr/bin/env bash
set -uo pipefail

cd "$(git rev-parse --show-toplevel)"

OUT="./melo_diagnostico.txt"
> "$OUT"

echo "==> Coletando arquivos + coverage em $OUT ..."

{
    echo "############################################"
    echo "# packages/catalog/__init__.py"
    echo "############################################"
    cat packages/catalog/__init__.py 2>/dev/null || echo "[arquivo não encontrado]"

    echo ""
    echo "############################################"
    echo "# packages/catalog/store.py"
    echo "############################################"
    cat packages/catalog/store.py 2>/dev/null || echo "[arquivo não encontrado]"

    echo ""
    echo "############################################"
    echo "# packages/adaptation/segmentation.py"
    echo "############################################"
    cat packages/adaptation/segmentation.py 2>/dev/null || echo "[arquivo não encontrado]"

    echo ""
    echo "############################################"
    echo "# packages/ai/adapter.py"
    echo "############################################"
    cat packages/ai/adapter.py 2>/dev/null || echo "[arquivo não encontrado]"

    echo ""
    echo "############################################"
    echo "# packages/ai/__init__.py"
    echo "############################################"
    cat packages/ai/__init__.py 2>/dev/null || echo "[arquivo não encontrado]"

    echo ""
    echo "############################################"
    echo "# packages/prompts/templates.py"
    echo "############################################"
    cat packages/prompts/templates.py 2>/dev/null || echo "[arquivo não encontrado]"

    echo ""
    echo "############################################"
    echo "# packages/prompts/__init__.py"
    echo "############################################"
    cat packages/prompts/__init__.py 2>/dev/null || echo "[arquivo não encontrado]"

    echo ""
    echo "############################################"
    echo "# tests/unit/test_catalog_store.py (teste já existente, pra eu não duplicar)"
    echo "############################################"
    cat tests/unit/test_catalog_store.py 2>/dev/null || echo "[arquivo não encontrado]"

    echo ""
    echo "############################################"
    echo "# tests/unit/test_segmentation.py (teste já existente)"
    echo "############################################"
    cat tests/unit/test_segmentation.py 2>/dev/null || echo "[arquivo não encontrado]"

    echo ""
    echo "############################################"
    echo "# tests/unit/test_ai_adapter.py (teste já existente)"
    echo "############################################"
    cat tests/unit/test_ai_adapter.py 2>/dev/null || echo "[arquivo não encontrado]"

    echo ""
    echo "############################################"
    echo "# COVERAGE REPORT (--cov-report=term-missing)"
    echo "############################################"
    pytest --cov=packages --cov-report=term-missing -q 2>&1 || true

} >> "$OUT"

echo ""
echo "==> Pronto. Exibindo o conteúdo completo abaixo pra você copiar direto:"
echo ""
cat "$OUT"
