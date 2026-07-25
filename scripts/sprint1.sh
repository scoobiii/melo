#!/usr/bin/env bash
set -euo pipefail

echo "=== MELO Sprint 1 ==="

python -m pip install -U pip

pip install \
ffmpeg-python \
mutagen \
librosa \
soundfile \
numpy \
scipy \
matplotlib \
pytest \
pytest-cov \
coverage \
ruff \
black \
mypy

mkdir -p \
packages/audio \
tests/unit \
logs \
reports \
output

touch \
packages/audio/__init__.py \
packages/audio/pipeline.py \
packages/audio/ingest.py \
packages/audio/metadata.py \
packages/audio/convert.py \
packages/audio/validate.py \
packages/audio/fingerprint.py

touch \
tests/unit/test_ingest.py \
tests/unit/test_metadata.py \
tests/unit/test_convert.py \
tests/unit/test_validate.py \
tests/unit/test_pipeline.py

ruff check . || true

black .

mypy packages || true

pytest \
--cov=packages/audio \
--cov-report=term \
--cov-report=html

git add .

git commit -m "feat(audio): bootstrap audio engine"

echo "Sprint 1 concluído."
