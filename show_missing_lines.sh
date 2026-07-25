#!/usr/bin/env bash
set -uo pipefail
cd "$(git rev-parse --show-toplevel)"

echo "==> Linhas não cobertas, com contexto (3 linhas antes/depois)"

show_range() {
    local file="$1"
    local start="$2"
    local end="$3"
    local ctx_start=$((start - 3))
    local ctx_end=$((end + 3))
    [ "$ctx_start" -lt 1 ] && ctx_start=1
    echo ""
    echo "---- $file : linhas $start-$end (contexto $ctx_start-$ctx_end) ----"
    sed -n "${ctx_start},${ctx_end}p" "$file" | nl -ba -v"$ctx_start"
}

show_range "packages/adaptation/features.py" 55 55
show_range "packages/adaptation/features.py" 66 66
show_range "packages/adaptation/features.py" 98 98
show_range "packages/adaptation/features.py" 104 104

show_range "packages/adaptation/segmentation.py" 51 51

show_range "packages/ai/adapter.py" 190 190

show_range "packages/catalog/store.py" 107 107
show_range "packages/catalog/store.py" 126 133
