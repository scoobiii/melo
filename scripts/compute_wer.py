#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# Arquivo         : compute_wer.py
# Diretorio       : scripts/
# Responsabilidade: Le output/wer_eval/template_ground_truth.txt (preenchido
#                    manualmente após ouvir os segmentos) + transcricoes
#                    do whisper.cpp, calcula Word Error Rate (WER) por
#                    segmento e agregado.
# Versao          : 1.0.0
# Data/hora       : 2026-07-27
# Autoria         : MELO / GOS3 - Scrum . Agile . DevOps
# Ciclo de vida   : PERSISTENTE — ferramenta de avaliação de qualidade.
#                    Sem input() bloqueante — le arquivos já preenchidos.
# -----------------------------------------------------------------------------
"""
Uso (depois de preencher output/wer_eval/template_ground_truth.txt):
    python scripts/compute_wer.py

WER = (substituições + inserções + deleções) / total de palavras no ground truth
Calculado via distância de edição (Levenshtein) a nível de palavra.
"""
import json
import re
import sys
from pathlib import Path

OUT_DIR = Path("output/wer_eval")


def normalizar(texto: str) -> list[str]:
    """Lowercase, remove pontuação, colapsa espaços — pra WER comparar
    conteúdo, não formatação."""
    texto = texto.lower()
    texto = re.sub(r"[^\w\sáéíóúñü]", "", texto, flags=re.UNICODE)
    return texto.split()


def word_error_rate(referencia: list[str], hipotese: list[str]) -> tuple[float, dict]:
    """Distância de edição a nível de palavra (Levenshtein), WER = edits / len(referencia)."""
    n, m = len(referencia), len(hipotese)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        dp[i][0] = i
    for j in range(m + 1):
        dp[0][j] = j
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if referencia[i - 1] == hipotese[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1])

    edits = dp[n][m]
    wer = edits / n if n > 0 else (0.0 if m == 0 else 1.0)
    return wer, {"edits": edits, "palavras_referencia": n, "palavras_hipotese": m}


def parse_template(caminho: Path) -> dict[int, str]:
    """Extrai 'GROUND_TRUTH_N: texto' do template preenchido."""
    conteudo = caminho.read_text(encoding="utf-8")
    resultado = {}
    for match in re.finditer(r"GROUND_TRUTH_(\d+):\s*(.*)", conteudo):
        indice = int(match.group(1))
        texto = match.group(2).strip()
        resultado[indice] = texto
    return resultado


def main():
    template_path = OUT_DIR / "template_ground_truth.txt"
    whisper_path = OUT_DIR / "transcricoes_whisper.json"

    if not template_path.exists() or not whisper_path.exists():
        print(f"Arquivos não encontrados em {OUT_DIR}/ — rode prepare_wer_eval.py primeiro.")
        sys.exit(1)

    ground_truth = parse_template(template_path)
    whisper = {int(k): v for k, v in json.loads(whisper_path.read_text(encoding="utf-8")).items()}

    vazios = [i for i, texto in ground_truth.items() if not texto]
    if vazios:
        print(f"AVISO: {len(vazios)} segmento(s) sem ground truth preenchido, ignorados: {vazios}")

    resultados = []
    for indice, texto_real in ground_truth.items():
        if not texto_real:
            continue
        if indice not in whisper:
            print(f"AVISO: segmento {indice} não tem transcrição do whisper — pulando.")
            continue

        ref = normalizar(texto_real)
        hip = normalizar(whisper[indice])
        wer, detalhe = word_error_rate(ref, hip)
        resultados.append((indice, wer, detalhe))
        print(f"  segmento {indice}: WER={wer:.2%}  ({detalhe['edits']} edits / {detalhe['palavras_referencia']} palavras)")

    if not resultados:
        print("Nenhum segmento avaliável (todos vazios ou sem par). Preencha o template e rode de novo.")
        sys.exit(1)

    total_edits = sum(d["edits"] for _, _, d in resultados)
    total_palavras = sum(d["palavras_referencia"] for _, _, d in resultados)
    wer_agregado = total_edits / total_palavras if total_palavras else 0.0

    print("")
    print(f"==> WER agregado ({len(resultados)} segmentos): {wer_agregado:.2%}")
    print("==> Referência de leitura: <10% é considerado bom pra transcrição em condições normais;")
    print("    15-25% é aceitável pra áudio ruidoso/mix; >30% indica problema real de qualidade.")


if __name__ == "__main__":
    main()
