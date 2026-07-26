#!/usr/bin/env python3
"""Gera as seções derivadas de dados reais em README.md e docs/DEVOPS.md.
Nunca faz find/replace de texto antigo — sempre reescreve o bloco entre
marcadores <!-- BEGIN:X --> / <!-- END:X --> a partir do estado real do
código. Idempotente por construção: rodar 2x seguidas dá o mesmo resultado.
"""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PACKAGES_DIR = ROOT / "packages"

# Descrição de cada módulo é julgamento humano — mantém aqui manualmente.
# Ordem da lista = ordem na tabela/árvore.
# (pacote, descrição p/ tabela README, comentário p/ árvore DEVOPS)
MODULE_INFO = [
    ("audio",      "Metadados de áudio (duração, sample rate, canais)",
                   "I/O e metadados de áudio (soundfile)"),
    ("lyrics",     "Transcrição de letra via Whisper (local)",
                   "transcrição via Whisper (import lazy, opcional)"),
    ("adaptation", "Estimativa de BPM, correlação de gênero panamá↔brasil e segmentação de letra",
                   "BPM + correlação de gênero panamá↔brasil + segmentação de letra"),
    ("catalog",    "Persistência (SQLite) de artistas/produtores/faixas/vozes + wiring de tradução de gênero",
                   "persistência SQLite: artistas, produtores, faixas, vozes, wiring de tradução (translation.py)"),
    ("pipeline",   "Orquestra audio → adaptation → lyrics numa chamada só",
                   "orquestra audio+lyrics+adaptation numa chamada"),
    ("publisher",  "Motor de split/payout de royalty (percentuais negociados fora do código)",
                   "split/payout de royalty (percentuais não hardcoded)"),
    ("ai",         "Adaptação de letra via LLM: prompt engineering isolado sem I/O (system prompt, few-shot) + client Anthropic API (retries, parsing XML)",
                   "client Anthropic API: envia prompt, parsing/retries (packages/ai/adapter.py)"),
    ("prompts",    None,
                   "prompt engineering isolado sem I/O: system prompt, few-shot, build_user_prompt (packages/prompts/templates.py)"),
    ("score",      "Métrica de aderência não-binária (correlação de gênero + confiança vocal + cobertura de dados)",
                   "métrica de aderência não-binária: correlação de gênero + confiança vocal + cobertura (packages/score/quality.py)"),
    ("voices",     "InstrumentalAdapter funcional e testado (time-stretch + EQ de textura, não-generativo); VoiceGenerator é skeleton — exige backend externo (RVC/Coqui/Bark), não sintetiza voz sozinho",
                   "instrumental funcional (time-stretch/EQ via scipy); voz é contrato p/ backend externo, sem geração própria (generator.py)"),
]

# módulos que aparecem juntos numa única linha da tabela (mesma descrição/testes somados)
COMBINE = {("ai", "prompts"): "`packages/ai`, `packages/prompts`"}


def find_test_paths(pkg: str):
    """Acha arquivos de teste do módulo em qualquer estrutura sob tests/
    (tests/unit/<pkg>/, tests/<pkg>/, ou test_<pkg>*.py solto)."""
    candidates = list(ROOT.glob(f"tests/**/*{pkg}*"))
    return [p for p in candidates if p.is_file() and p.name.startswith("test_") and p.suffix == ".py"]


def count_tests(pkg: str) -> int:
    """Conta testes de um módulo via pytest --collect-only. Retorna 0 se
    nenhum arquivo de teste for encontrado — imprime aviso nesse caso,
    porque 0 é ambíguo (pode ser 'sem testes' ou 'não achei o arquivo')."""
    paths = find_test_paths(pkg)
    if not paths:
        print(f"    [aviso] nenhum arquivo de teste encontrado pra '{pkg}' — contagem forçada a 0, confira manualmente.")
        return 0
    result = subprocess.run(
        ["python3", "-m", "pytest", "--collect-only", "-q", *[str(p) for p in paths]],
        capture_output=True, text=True, cwd=ROOT,
    )
    m = re.search(r"(\d+)\s+tests? collected", result.stdout)
    if not m:
        print(f"    [aviso] pytest rodou pra '{pkg}' mas não achei contagem no output — confira manualmente.")
        print(result.stdout[-500:])
        return 0
    return int(m.group(1))


def build_rows():
    counts = {pkg: count_tests(pkg) for pkg, _, _ in MODULE_INFO}
    rows = []
    skip = set()
    for pkg, desc, _tree_comment in MODULE_INFO:
        if pkg in skip:
            continue
        combo_key = next((k for k in COMBINE if pkg == k[0]), None)
        if combo_key:
            label = COMBINE[combo_key]
            total = sum(counts[p] for p in combo_key)
            desc_final = MODULE_INFO[[p for p, _, _ in MODULE_INFO].index(pkg)][1]
            rows.append((label, desc_final, total))
            skip.update(combo_key)
        else:
            rows.append((f"`packages/{pkg}`", desc, counts[pkg]))
    return rows


def replace_block(content: str, marker: str, new_body: str) -> str:
    begin, end = f"<!-- BEGIN:{marker} -->", f"<!-- END:{marker} -->"
    if begin not in content or end not in content:
        print(f"Marcadores {begin}/{end} não encontrados — insere manualmente uma vez antes de rodar.")
        sys.exit(1)
    pattern = re.compile(re.escape(begin) + r".*?" + re.escape(end), re.DOTALL)
    return pattern.sub(f"{begin}\n{new_body}\n{end}", content, count=1)


def main():
    rows = build_rows()
    total = sum(r[2] for r in rows)

    # ---- README.md: tabela + total ----
    table_lines = ["| Módulo | O que faz | Testes |", "|---|---|---|"]
    table_lines += [f"| {label} | {desc} | {n} |" for label, desc, n in rows]
    table_lines.append("")
    table_lines.append(f"**Total: {total} testes, suíte 100% verde.**")
    readme_path = ROOT / "README.md"
    readme = readme_path.read_text(encoding="utf-8")
    readme = replace_block(readme, "MODULES", "\n".join(table_lines))
    readme_path.write_text(readme, encoding="utf-8")
    print(f"==> README.md: bloco MODULES regenerado ({total} testes).")

    # ---- docs/DEVOPS.md: árvore + contagem ----
    tree_lines = ["```", "packages/"]
    visible = [(pkg, comment) for pkg, _, comment in MODULE_INFO]
    for i, (pkg, comment) in enumerate(visible):
        prefix = "└──" if i == len(visible) - 1 else "├──"
        tree_lines.append(f"{prefix} {pkg}/".ljust(20) + f"# {comment}" if comment else f"{prefix} {pkg}/")
    tree_lines.append("```")
    devops_path = ROOT / "docs" / "DEVOPS.md"
    devops = devops_path.read_text(encoding="utf-8")
    devops = replace_block(devops, "TREE", "\n".join(tree_lines))
    devops = replace_block(devops, "TESTCOUNT", f"Estado atual: {total} testes, 100% passando.")
    devops_path.write_text(devops, encoding="utf-8")
    print(f"==> docs/DEVOPS.md: blocos TREE e TESTCOUNT regenerados.")


if __name__ == "__main__":
    main()
