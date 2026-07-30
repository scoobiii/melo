#!/data/data/com.termux/files/usr/bin/bash

set -Eeuo pipefail

cd "$HOME/MELO"

INPUT="$(
    find . \
        -maxdepth 2 \
        -type f \
        -name 'melo-transcription-*.json' \
        -printf '%T@ %p\n' \
    | sort -nr \
    | head -n 1 \
    | cut -d' ' -f2-
)"

if [ -z "${INPUT:-}" ]; then
    echo "ERRO: nenhum melo-transcription-*.json encontrado."
    exit 1
fi

echo "Entrada: $INPUT"

python \
    packages/catalog/validate_catalog.py \
    "$INPUT"
