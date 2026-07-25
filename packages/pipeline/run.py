"""Pipeline de integração: audio -> lyrics -> adaptation.

Orquestra os módulos já testados isoladamente numa única chamada,
com falha graciosa na etapa de transcrição (Whisper pode não estar
instalado no ambiente — o pipeline continua e reporta a ausência
em vez de quebrar).
"""
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from packages.adaptation.correlator import correlate_genre
from packages.adaptation.features import extract_features
from packages.audio.loader import load_audio_info


@dataclass
class PipelineResult:
    audio_path: str
    duration_seconds: float
    sample_rate: int
    channels: int
    bpm: float
    genero_origem: str
    correlacoes: List[Tuple[str, float]] = field(default_factory=list)
    transcricao: Optional[str] = None
    transcricao_erro: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "audio_path": self.audio_path,
            "duration_seconds": round(self.duration_seconds, 2),
            "sample_rate": self.sample_rate,
            "channels": self.channels,
            "bpm": self.bpm,
            "genero_origem": self.genero_origem,
            "correlacoes": [
                {"genero": nome, "score": score} for nome, score in self.correlacoes
            ],
            "transcricao": self.transcricao,
            "transcricao_erro": self.transcricao_erro,
        }


def run_pipeline(
    audio_path: str,
    genero_origem: str,
    modelo_whisper: str = "small",
    idioma: str = "pt",
    transcrever: bool = True,
) -> PipelineResult:
    """Roda o pipeline completo sobre um arquivo de áudio real.

    1. Carrega metadados do áudio (packages.audio)
    2. Extrai BPM aproximado (packages.adaptation.features)
    3. Correlaciona com gêneros da outra região (packages.adaptation.correlator)
    4. (Opcional) Transcreve a letra via Whisper (packages.lyrics) — se falhar
       (ex.: Whisper não instalado), reporta o erro sem interromper o pipeline.
    """
    info = load_audio_info(audio_path)
    features = extract_features(audio_path)
    correlacoes = correlate_genre(genero_origem, bpm=features.bpm)
    correlacoes_simples = [(g.name, score) for g, score in correlacoes]

    transcricao = None
    transcricao_erro = None
    if transcrever:
        try:
            from packages.lyrics.transcriber import transcribe_audio
            transcricao = transcribe_audio(audio_path, modelo=modelo_whisper, idioma=idioma)
        except Exception as e:  # noqa: BLE001 - queremos capturar qualquer falha de dependência/modelo
            transcricao_erro = f"{type(e).__name__}: {e}"

    return PipelineResult(
        audio_path=audio_path,
        duration_seconds=info.duration_seconds,
        sample_rate=info.sample_rate,
        channels=info.channels,
        bpm=features.bpm,
        genero_origem=genero_origem,
        correlacoes=correlacoes_simples,
        transcricao=transcricao,
        transcricao_erro=transcricao_erro,
    )
