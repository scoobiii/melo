"""Audio-to-text transcription via Whisper (local, no API calls)."""
from pathlib import Path
from typing import Optional

MODELOS_VALIDOS = ("tiny", "base", "small", "medium", "large")


def transcribe_audio(
    arquivo: str,
    modelo: str = "small",
    idioma: str = "pt",
) -> str:
    """Transcribe an audio file to text using a local Whisper model.

    Raises:
        FileNotFoundError: if `arquivo` does not exist.
        ValueError: if `modelo` is not a valid Whisper model size.
    """
    if modelo not in MODELOS_VALIDOS:
        raise ValueError(f"Modelo inválido: {modelo}. Use um de {MODELOS_VALIDOS}")

    caminho = Path(arquivo)
    if not caminho.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")

    import whisper  # pip install openai-whisper (lazy: só carrega se realmente for transcrever)

    model = whisper.load_model(modelo)
    resultado = model.transcribe(str(caminho), language=idioma, verbose=False)
    return resultado["text"].strip()


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
