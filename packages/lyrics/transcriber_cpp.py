# Localização no repo: packages/lyrics/transcriber_cpp.py
"""
Transcrição via whisper.cpp (binário `whisper-cli` compilado local),
como alternativa a transcriber.py quando faster-whisper não instala.

Motivo de existir: em 2026-07-25, `pip install faster-whisper` falhou
neste ambiente (Termux, Python 3.14) porque sua dependência `av` não
compila — erro de incompatibilidade Cython/`noexcept` no pacote `av`
10.x/11.x/12.x contra Python 3.14, não relacionado a ARM/Android
especificamente. Ou seja: a premissa do comentário em transcriber.py
("faster-whisper é mais estável em Termux/Android ARM64") não se
confirmou neste ambiente — faster-whisper também falhou, por motivo
diferente do torch (Cython vs Python 3.14, não Rust vs Android triple).

whisper.cpp foi validado funcionando de ponta a ponta neste mesmo
ambiente: compila com clang (já presente), roda modelo 'small' com
qualidade aceitável, ~18s para 15s de áudio em CPU de telefone.

Mesma interface pública de transcriber.py (transcribe_audio,
transcribe_and_save) de propósito — troca de implementação é drop-in,
sem exigir mudança em packages/pipeline/run.py.

Pré-requisito (não instalado por este módulo):
    cd ~ && git clone https://github.com/ggerganov/whisper.cpp
    cd whisper.cpp && cmake -B build && cmake --build build --config Release
    bash ./models/download-ggml-model.sh small
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Optional

MODELOS_VALIDOS = ("tiny", "base", "small", "medium", "large-v3")

# Configuráveis via env var para não hardcodar caminho de usuário.
WHISPER_CPP_BIN = Path(
    os.environ.get(
        "WHISPER_CPP_BIN",
        str(Path.home() / "whisper.cpp" / "build" / "bin" / "whisper-cli"),
    )
)
WHISPER_CPP_MODEL_DIR = Path(
    os.environ.get("WHISPER_CPP_MODEL_DIR", str(Path.home() / "whisper.cpp" / "models"))
)


def _model_path(modelo: str) -> Path:
    return WHISPER_CPP_MODEL_DIR / f"ggml-{modelo}.bin"


def transcribe_audio(
    arquivo: str,
    modelo: str = "small",
    idioma: str = "pt",
) -> str:
    """Transcribe an audio file to text using a local whisper.cpp binary.

    Raises:
        FileNotFoundError: if `arquivo`, o binário whisper-cli, ou o
            arquivo de modelo não existirem.
        ValueError: if `modelo` is not a valid Whisper model size.
        RuntimeError: se o processo whisper-cli sair com erro.
    """
    if modelo not in MODELOS_VALIDOS:
        raise ValueError(f"Modelo inválido: {modelo}. Use um de {MODELOS_VALIDOS}")

    caminho = Path(arquivo)
    if not caminho.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")

    if not WHISPER_CPP_BIN.exists():
        raise FileNotFoundError(
            f"Binário whisper-cli não encontrado em {WHISPER_CPP_BIN}. "
            "Compile whisper.cpp primeiro (ver docstring do módulo) ou "
            "defina WHISPER_CPP_BIN apontando para o binário."
        )

    modelo_path = _model_path(modelo)
    if not modelo_path.exists():
        raise FileNotFoundError(
            f"Modelo '{modelo}' não encontrado em {modelo_path}. "
            f"Baixe com: bash whisper.cpp/models/download-ggml-model.sh {modelo}"
        )

    resultado = subprocess.run(
        [
            str(WHISPER_CPP_BIN),
            "-m", str(modelo_path),
            "-f", str(caminho),
            "-l", idioma,
            "-nt",  # no timestamps -- só texto puro na saída
        ],
        capture_output=True,
        text=True,
    )

    if resultado.returncode != 0:
        raise RuntimeError(
            f"whisper-cli saiu com código {resultado.returncode}: "
            f"{resultado.stderr[-500:]}"
        )

    return resultado.stdout.strip()


def transcribe_and_save(
    arquivo: str,
    modelo: str = "small",
    idioma: str = "pt",
    saida: Optional[str] = None,
) -> Path:
    """Transcribe an audio file and write the result to a .txt file. Returns the output path."""
    texto = transcribe_audio(arquivo, modelo=modelo, idioma=idioma)
    caminho_saida = Path(saida) if saida else Path(arquivo).with_suffix(".txt")
    caminho_saida.write_text(texto, encoding="utf-8")
    return caminho_saida
