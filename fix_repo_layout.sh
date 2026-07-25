#!/usr/bin/env bash
set -euo pipefail

echo "==> MELO :: corrigindo layout de docs + commitando código-fonte"

cd "$(git rev-parse --show-toplevel)"
echo "==> Raiz do repo: $(pwd)"

# 1. Corrigir arquivos que foram criados no lugar errado
if [ -f docs/README.md ]; then
    mv docs/README.md README.md
    echo "==> docs/README.md -> README.md (raiz)"
fi

if [ -d docs/docs ]; then
    [ -f docs/docs/DEVOPS.md ] && mv docs/docs/DEVOPS.md docs/DEVOPS.md
    [ -f docs/docs/USER_GUIDE.md ] && mv docs/docs/USER_GUIDE.md docs/USER_GUIDE.md
    rmdir docs/docs 2>/dev/null || true
    echo "==> docs/docs/* -> docs/* (corrigido)"
fi

# 2. Remover os scripts de bootstrap/patch da raiz do controle de versão
#    (são artefatos de desenvolvimento, não código do produto — mas ficam
#    no disco, só não versionados; ver docs/DEVOPS.md sobre isso)
cat > .gitignore << 'EOF'
__pycache__/
*.pyc
.pytest_cache/
htmlcov/
.coverage
server.log
bootstrap_*.sh
patch_*.sh
find_audio_samples.sh
assets/samples/*.mp3
assets/samples/*.wav
output/*.json
EOF
echo "==> .gitignore criado/atualizado"

# 3. Adicionar TUDO que representa o projeto real: código + testes + docs
git add README.md docs/ .gitignore
git add packages/ tests/ scripts/ requirements/ pyproject.toml Makefile 2>/dev/null || true

echo ""
echo "==> git status:"
git status --short

if git diff --cached --quiet; then
    echo "==> Nada para commitar."
else
    git commit -m "fix: corrige layout de docs criados no caminho errado

Move README.md e docs/*.md para os caminhos corretos (script anterior
rodou de dentro de docs/, duplicando o caminho). Adiciona ao versionamento
o código-fonte que ainda não estava rastreado: packages/ (5 módulos:
audio, lyrics, adaptation, pipeline, publisher), tests/unit/ (32 testes),
scripts/run_pipeline.py, requirements/*.txt. Adiciona .gitignore para
excluir artefatos de desenvolvimento (bootstrap/patch scripts, cache,
samples de áudio, output gerado)."
    echo "==> Commit criado."
fi

echo ""
echo "==> Estrutura final de docs:"
ls -la README.md docs/ 2>/dev/null

echo ""
echo "==> Próximo passo (requer sua autenticação do GitHub):"
if git remote get-url origin >/dev/null 2>&1; then
    echo "    git push origin main"
else
    echo "    git remote add origin https://github.com/scoobiii/melo.git"
    echo "    git branch -M main"
    echo "    git push -u origin main"
fi
