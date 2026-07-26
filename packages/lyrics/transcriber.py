"""Audio-to-text transcription via faster-whisper (local, no API calls).

Usa faster-whisper (CTranslate2) em vez de openai-whisper por decisão
deliberada: openai-whisper traz torch + numba/llvmlite como dependências,
que exigem compilação nativa e são historicamente instáveis em
Termux/Android ARM64 (mesmo motivo pelo qual packages/adaptation evita
librosa/numba - ver docs/DEVOPS.md). faster-whisper usa o mesmo modelo
Whisper, mas via CTranslate2, sem numba/llvmlite.
"""
from pathlib import Path
from typing import Optional

MODELOS_VALIDOS = ("tiny", "base", "small", "medium", "large-v3")


def transcribe_audio(
    arquivo: str,
    modelo: str = "small",
    idioma: str = "pt",
) -> str:
    """Transcribe an audio file to text using a local faster-whisper model.

    Raises:
        FileNotFoundError: if `arquivo` does not exist.
        ValueError: if `modelo` is not a valid Whisper model size.
    """
    if modelo not in MODELOS_VALIDOS:
        raise ValueError(f"Modelo inválido: {modelo}. Use um de {MODELOS_VALIDOS}")

    caminho = Path(arquivo)
    if not caminho.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")

    from faster_whisper import WhisperModel  # lazy: só carrega se for transcrever

    model = WhisperModel(modelo, device="cpu", compute_type="int8")
    segments, _info = model.transcribe(str(caminho), language=idioma)
    texto = " ".join(segment.text.strip() for segment in segments)
    return texto.strip()


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
