#!/usr/bin/env python3
"""
scripts/update_docs.py

Atualiza README.md e docs/BACKLOG.md de forma idempotente:
  - backup .bak de cada arquivo antes de tocar
  - adiciona seção "Fluxo atual do projeto" ao README (só se ainda não existir)
  - remove duplicata exata do bloco "Arielis Nicole" no BACKLOG (sem truncar
    o resto do arquivo -- bug do script bash anterior)
  - adiciona entrada sobre validate_catalog.py no BACKLOG (só se ainda não existir)
  - adiciona bloco "Sessão de engenharia — <data>" no BACKLOG (só se ainda
    não existir um para a data de hoje)

NÃO faz git add/commit/push. Uso:
    cd ~/MELO
    python3 scripts/update_docs.py
"""
from __future__ import annotations

import subprocess
from datetime import date
from pathlib import Path

ROOT = Path.home() / "MELO"
README = ROOT / "README.md"
BACKLOG = ROOT / "docs" / "BACKLOG.md"


def backup(path: Path) -> None:
    bak = path.with_suffix(path.suffix + ".bak")
    bak.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"  backup: {bak}")


def git_commit_curto() -> str:
    try:
        resultado = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=ROOT, capture_output=True, text=True, timeout=5,
        )
        if resultado.returncode == 0:
            return resultado.stdout.strip()
    except (subprocess.SubprocessError, OSError):
        pass
    return "N/A"


FLUXO_README = """
---

## Fluxo atual do projeto

```
Áudio
  ↓ whisper.cpp (small)
Transcrição
  ↓ Curadoria manual (tracklist)
merge_tracklist_into_whisper.py
  ↓
validate_catalog.py (MusicBrainz)
  ↓
SQLite / JSON / CSV
```

### Comandos principais

```bash
make help
make install
make test
make catalog
```

O `validate_catalog.py` **não realiza fingerprinting**. Ele utiliza
artista/título previamente obtidos por transcrição e/ou curadoria manual
para validar e enriquecer metadados usando a API oficial do MusicBrainz.
"""

ENTRADA_VALIDATE_CATALOG = """
- ✅ validate_catalog.py criado.
  - Normaliza artista/título.
  - Consulta MusicBrainz.
  - Calcula score de confiança.
  - Exporta JSON, CSV, SQLite e relatório.
  - Não realiza fingerprinting.
  - Utiliza catálogo previamente obtido por transcrição/curadoria.
"""

MARKER_ARIELIS = "## Concluido (28/07) - resolvido o misterio"


def dedupe_secao_duplicada(txt: str, marker: str) -> str:
    """Remove uma segunda ocorrência EXATA e consecutiva de um bloco de
    seção, sem tocar no resto do arquivo (bug do script anterior: ele
    cortava tudo depois do segundo marcador, perdendo conteúdo real)."""
    idx1 = txt.find(marker)
    if idx1 == -1:
        return txt

    idx2 = txt.find(marker, idx1 + len(marker))
    if idx2 == -1:
        return txt  # só uma ocorrência, nada a fazer

    bloco1 = txt[idx1:idx2]

    proximo_header = txt.find("\n## ", idx2 + len(marker))
    fim2 = proximo_header + 1 if proximo_header != -1 else len(txt)
    bloco2 = txt[idx2:fim2]

    if bloco1.strip() == bloco2.strip():
        txt = txt[:idx2] + txt[fim2:]
        print("  BACKLOG: duplicata do bloco 'Arielis Nicole' removida")
    else:
        print("  BACKLOG: dois blocos com o marcador, mas conteúdo "
              "diferente -- não removi nada automaticamente, confira manual")

    return txt


def atualizar_readme() -> None:
    if not README.exists():
        print(f"ERRO: {README} não encontrado.")
        raise SystemExit(1)

    backup(README)
    txt = README.read_text(encoding="utf-8")

    if "validate_catalog.py" in txt:
        print("  README: seção 'Fluxo atual' já existe, nada a fazer")
        return

    txt = txt.rstrip() + "\n" + FLUXO_README
    README.write_text(txt, encoding="utf-8")
    print("  README: seção 'Fluxo atual do projeto' adicionada")


def atualizar_backlog() -> None:
    if not BACKLOG.exists():
        print(f"ERRO: {BACKLOG} não encontrado.")
        raise SystemExit(1)

    backup(BACKLOG)
    txt = BACKLOG.read_text(encoding="utf-8")

    txt = dedupe_secao_duplicada(txt, MARKER_ARIELIS)

    if "validate_catalog.py criado" not in txt:
        txt = txt.rstrip() + "\n" + ENTRADA_VALIDATE_CATALOG
        print("  BACKLOG: entrada sobre validate_catalog.py adicionada")
    else:
        print("  BACKLOG: entrada sobre validate_catalog.py já existe")

    data_hoje = date.today().strftime("%d/%m/%Y")
    marcador_sessao = f"## Sessão de engenharia — {data_hoje}"

    if marcador_sessao not in txt:
        commit = git_commit_curto()
        bloco_sessao = f"""
{marcador_sessao}

Commit de referência: `{commit}`

### Decisões

- Padronização definitiva do diretório `output/`.
- Inclusão do `validate_catalog.py`.
- MusicBrainz adotado para validação e enriquecimento de metadados.
- whisper.cpp (`small`) permanece como fluxo recomendado.
- Curadoria manual continua sendo a fonte de verdade para identificação de artistas.

Arquitetura consolidada:

```
Áudio
  ↓ whisper.cpp
Curadoria manual
  ↓
merge_tracklist_into_whisper.py
  ↓
validate_catalog.py
  ↓
SQLite / JSON / CSV
```
"""
        txt = txt.rstrip() + "\n" + bloco_sessao
        print(f"  BACKLOG: bloco de sessão ({data_hoje}) adicionado")
    else:
        print(f"  BACKLOG: bloco de sessão ({data_hoje}) já existe")

    BACKLOG.write_text(txt, encoding="utf-8")


def main() -> int:
    print("=" * 40)
    print(" MELO Documentation Updater (Python)")
    print("=" * 40)

    print("\nREADME:")
    atualizar_readme()

    print("\nBACKLOG:")
    atualizar_backlog()

    print("\nArquivos atualizados:")
    print(f"  {README}")
    print(f"  {BACKLOG}")

    print("\nPróximos passos (manuais, este script não commita nada):")
    print("  git diff")
    print("  git add README.md docs/BACKLOG.md")
    print('  git commit -m "docs: atualiza README e BACKLOG"')

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
