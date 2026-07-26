"""
tests/unit/test_voices_generator.py

Testes de packages/voices/generator.py (Fase 1 do ROADMAP — esqueleto
funcional + stubs de integração).

Nota sobre execução: estes testes usam numpy/scipy/soundfile reais (mesmas
dependências que o próprio generator.py já usa), não fakes — não faz sentido
mockar o processamento de áudio que é justamente o que queremos validar.
Isso significa que precisam do ambiente real do projeto (Termux com essas
libs instaladas) para rodar; não foram executados no sandbox de geração
deste arquivo por falta dessas dependências ali.
"""

import numpy as np
import pytest

from packages.voices.generator import (
    GeneratedTrack,
    InstrumentalAdapter,
    VoiceGenerationError,
    VoiceGenerator,
)


@pytest.fixture
def synthetic_wav(tmp_path):
    """Gera um WAV sintético (seno de 220Hz, 2s) para testar o adapter sem
    depender de nenhum arquivo de áudio real do usuário."""
    import soundfile as sf

    sr = 22050
    duration = 2.0
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    y = (0.5 * np.sin(2 * np.pi * 220 * t)).astype(np.float32)

    path = tmp_path / "entrada.wav"
    sf.write(str(path), y, sr)
    return str(path), sr, duration


class TestInstrumentalAdapter:
    def test_adapt_produces_output_file(self, synthetic_wav, tmp_path):
        path, sr, _duration = synthetic_wav
        saida = tmp_path / "saida.wav"
        adapter = InstrumentalAdapter()

        resultado = adapter.adapt(
            audio_path=path,
            target_bpm=120.0,
            source_bpm=100.0,
            output_path=str(saida),
        )

        assert saida.exists()
        assert isinstance(resultado, GeneratedTrack)
        assert resultado.sample_rate == sr

    def test_adapt_stretches_duration_inversely_to_bpm_ratio(self, synthetic_wav, tmp_path):
        path, _sr, duration_original = synthetic_wav
        saida = tmp_path / "saida.wav"
        adapter = InstrumentalAdapter()

        # target_bpm > source_bpm => ratio > 1 => áudio "acelera" => encurta
        resultado = adapter.adapt(
            audio_path=path,
            target_bpm=200.0,
            source_bpm=100.0,
            output_path=str(saida),
        )

        assert resultado.duration_seconds < duration_original

    def test_adapt_slows_duration_when_target_bpm_lower(self, synthetic_wav, tmp_path):
        path, _sr, duration_original = synthetic_wav
        saida = tmp_path / "saida.wav"
        adapter = InstrumentalAdapter()

        # target_bpm < source_bpm => ratio < 1 => "desacelera" => alonga
        resultado = adapter.adapt(
            audio_path=path,
            target_bpm=50.0,
            source_bpm=100.0,
            output_path=str(saida),
        )

        assert resultado.duration_seconds > duration_original

    def test_adapt_known_bug_genre_fields_always_empty(self, synthetic_wav, tmp_path):
        """DOCUMENTA UM BUG CONHECIDO, não um comportamento desejado.

        adapt() não recebe source_genre/target_genre como parâmetro e sempre
        retorna string vazia nesses dois campos do GeneratedTrack. Este teste
        deve PASSAR hoje (confirmando o bug) e FALHAR assim que o fix for
        aplicado — nesse momento, troque as duas asserções por checagem dos
        valores reais passados.
        """
        path, _sr, _duration = synthetic_wav
        saida = tmp_path / "saida.wav"
        adapter = InstrumentalAdapter()

        resultado = adapter.adapt(
            audio_path=path,
            target_bpm=120.0,
            source_bpm=100.0,
            output_path=str(saida),
        )

        assert resultado.source_genre == ""
        assert resultado.target_genre == ""

    def test_adapt_percussivo_texture_does_not_crash(self, synthetic_wav, tmp_path):
        path, _sr, _duration = synthetic_wav
        saida = tmp_path / "saida.wav"
        adapter = InstrumentalAdapter()

        adapter.adapt(
            audio_path=path,
            target_bpm=120.0,
            source_bpm=100.0,
            output_path=str(saida),
            texture="percussivo_forte",
        )

        assert saida.exists()

    def test_adapt_romantico_texture_does_not_crash(self, synthetic_wav, tmp_path):
        path, _sr, _duration = synthetic_wav
        saida = tmp_path / "saida.wav"
        adapter = InstrumentalAdapter()

        adapter.adapt(
            audio_path=path,
            target_bpm=120.0,
            source_bpm=100.0,
            output_path=str(saida),
            texture="romantico_suave",
        )

        assert saida.exists()

    def test_adapt_creates_parent_directories(self, synthetic_wav, tmp_path):
        path, _sr, _duration = synthetic_wav
        saida = tmp_path / "sub1" / "sub2" / "saida.wav"
        adapter = InstrumentalAdapter()

        adapter.adapt(
            audio_path=path,
            target_bpm=120.0,
            source_bpm=100.0,
            output_path=str(saida),
        )

        assert saida.exists()


class TestVoiceGenerator:
    def test_generate_without_backend_raises_with_licensing_warning(self):
        gerador = VoiceGenerator()

        with pytest.raises(VoiceGenerationError, match="licença explícita"):
            gerador.generate(
                lyrics="letra qualquer",
                target_genre="forro_pe_de_serra",
                bpm=95.0,
                output_path="saida.wav",
            )

    def test_generate_with_backend_returns_generated_track(self, tmp_path):
        import soundfile as sf

        sr = 22050
        y = np.zeros(sr, dtype=np.float32)
        saida = tmp_path / "voz.wav"
        sf.write(str(saida), y, sr)

        def fake_backend(lyrics, target_genre, bpm, output_path, reference_audio):
            return str(saida)

        gerador = VoiceGenerator(backend=fake_backend)
        resultado = gerador.generate(
            lyrics="letra qualquer",
            target_genre="forro_pe_de_serra",
            bpm=95.0,
            output_path=str(saida),
        )

        assert isinstance(resultado, GeneratedTrack)
        assert resultado.target_genre == "forro_pe_de_serra"
        assert resultado.bpm_target == 95.0
        assert resultado.notes == "Gerado por backend injetado"

    def test_generate_with_backend_passes_reference_audio_through(self, tmp_path):
        import soundfile as sf

        sr = 22050
        y = np.zeros(sr, dtype=np.float32)
        saida = tmp_path / "voz.wav"
        sf.write(str(saida), y, sr)

        recebido = {}

        def fake_backend(lyrics, target_genre, bpm, output_path, reference_audio):
            recebido["reference_audio"] = reference_audio
            return str(saida)

        gerador = VoiceGenerator(backend=fake_backend)
        gerador.generate(
            lyrics="letra",
            target_genre="forro_pe_de_serra",
            bpm=95.0,
            output_path=str(saida),
            reference_audio="referencia_de_textura.wav",
        )

        assert recebido["reference_audio"] == "referencia_de_textura.wav"
