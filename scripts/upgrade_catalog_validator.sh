#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FILE="$ROOT/packages/catalog/validate_catalog.py"

[ -f "$FILE" ] || {
    echo "Arquivo não encontrado:"
    echo "$FILE"
    exit 1
}

echo "== Atualizando validate_catalog.py =="

# ------------------------------------------------------------------
# output/ (padronização)
# ------------------------------------------------------------------

sed -i \
    's|OUTPUT_DIR = Path("outputs")|OUTPUT_DIR = Path("output")|g' \
    "$FILE"

# ------------------------------------------------------------------
# Docstring
# ------------------------------------------------------------------

python3 <<'PY'
from pathlib import Path
import re

f = Path("packages/catalog/validate_catalog.py")
text = f.read_text(encoding="utf-8")

novo = '''"""
MELO — Music Catalog Validator

Objetivo
---------
Validar e enriquecer um catálogo previamente obtido por
transcrição e/ou curadoria manual.

Este script NÃO realiza fingerprinting de áudio.

Ele utiliza artista e título previamente conhecidos para
consultar catálogos públicos (MusicBrainz) e recuperar
metadados oficiais como:

- Recording
- Artist
- Release
- Release Date
- ISRC
- MBIDs

Entrada
--------
melo-transcription-*.json

Saídas
------
output/catalogo_validado.json
output/catalogo_validado.csv
output/catalogo_validado.sqlite
output/pendencias_catalogo.json
output/relatorio_catalogo.md
"""'''

text = re.sub(r'""".*?"""', novo, text, count=1, flags=re.S)

f.write_text(text, encoding="utf-8")
PY

echo "OK"
