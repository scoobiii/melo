# tests/test_audio_validate.py
import pytest
import tempfile
import os
from pathlib import Path
import wave
import struct

from packages.audio.validate import AudioValidator, validate_audio_input

class TestAudioValidator:
    """Test suite for audio validation module with 100% coverage."""
    
    @pytest.fixture
    def validator(self):
        return AudioValidator()
    
    @pytest.fixture
    def temp_wav_file(self):
        """Create temporary valid WAV file for testing using built-in modules."""
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            # Create simple WAV file using built-in wave module
            with wave.open(f.name, 'wb') as w:
                w.setnchannels(1)  # Mono
                w.setsampwidth(2)  # 16-bit
                w.setframerate(44100)  # 44.1kHz
                # Generate simple tone data
                data = b'\x00\x00' * 44100  # 1 second of silence
                w.writeframes(data)
            yield Path(f.name)
        os.unlink(f.name)
    
    def test_supported_formats_validation(self, validator):
        """Test supported audio formats."""
        assert len(validator.SUPPORTED_FORMATS) >= 3
        assert '.wav' in validator.SUPPORTED_FORMATS
        assert '.flac' in validator.SUPPORTED_FORMATS
    
    def test_file_exists_validation(self, validator):
        """Test validation of non-existent files."""
        is_valid, msg = validator.validate_file("nonexistent.wav")
        assert not is_valid
        assert "does not exist" in msg
    
    def test_unsupported_format(self, validator):
        """Test unsupported file format rejection."""
        with tempfile.NamedTemporaryFile(suffix='.txt') as f:
            is_valid, msg = validator.validate_file(f.name)
            assert not is_valid
            assert "Unsupported format" in msg
    
    def test_file_too_large(self, validator, temp_wav_file, monkeypatch):
        """Test file size limit validation.

        Path.stat virou atributo read-only em instâncias no Python 3.14
        (PosixPath usa __slots__) — atribuição direta como
        `temp_wav_file.stat = lambda: ...` quebra com AttributeError.
        Fix: monkeypatch.setattr no nível da classe Path, restaurado
        automaticamente no teardown do monkeypatch (escopo por teste).
        """
        class _FakeStat:
            st_size = 200 * 1024 * 1024

        monkeypatch.setattr(Path, "stat", lambda self: _FakeStat())

        is_valid, msg = validator.validate_file(temp_wav_file)
        assert not is_valid
        assert "File too large" in msg
    
    def test_valid_audio_file(self, validator, temp_wav_file):
        """Test validation of valid audio file."""
        is_valid, msg = validator.validate_file(temp_wav_file)
        assert is_valid
        assert msg == "Valid"
    
    def test_corrupted_wav_file(self, validator):
        """Test validation of corrupted WAV file."""
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            # Write invalid WAV data
            f.write(b"invalid wav data")
            corrupted_file = f.name
        
        try:
            is_valid, msg = validator.validate_file(corrupted_file)
            assert not is_valid
            assert "Corrupted" in msg
        finally:
            os.unlink(corrupted_file)
    
    def test_empty_audio_file(self, validator):
        """Test validation of empty audio file."""
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            # Create empty WAV with proper header
            with wave.open(f.name, 'wb') as w:
                w.setnchannels(1)
                w.setsampwidth(2)
                w.setframerate(44100)
            empty_file = f.name
        
        try:
            is_valid, msg = validator.validate_file(empty_file)
            assert not is_valid
            assert "Empty audio file" in msg
        finally:
            os.unlink(empty_file)
    
    def test_sample_rate_validation(self, validator):
        """Test WAV creation with valid sample rate."""
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            with wave.open(f.name, 'wb') as w:
                w.setnchannels(1)
                w.setsampwidth(2)
                w.setframerate(8000)  # Minimum valid rate
                w.writeframes(b'\x00\x00' * 8000)  # 1 second of data
            valid_sr_file = f.name
        
        try:
            is_valid, msg = validator.validate_file(valid_sr_file)
            assert is_valid  # Should be valid with 8000Hz
        finally:
            os.unlink(valid_sr_file)
    
    def test_validation_cache_functionality(self, validator, temp_wav_file):
        """Test validation caching mechanism."""
        # First validation
        result1 = validator.validate_file(temp_wav_file)
        cache_size_after_first = len(validator.validation_cache)
        
        # Second validation (should use cache)
        result2 = validator.validate_file(temp_wav_file)
        
        assert result1 == result2
        assert cache_size_after_first == 1
        assert str(temp_wav_file) in validator.validation_cache
    
    def test_batch_validation_performance(self, validator, tmp_path):
        """Test batch validation functionality com 5 arquivos distintos.

        (Reescrito: a versão original passava o mesmo path 5x esperando
        5 entradas em 'results', mas validate_batch indexa por
        str(filepath) — paths repetidos colapsam num resultado só. Ver
        test_batch_validation_deduplicates_repeated_path abaixo, que
        documenta esse comportamento como intencional.)
        """
        files = []
        for i in range(5):
            wav_path = tmp_path / f"track_{i}.wav"
            with wave.open(str(wav_path), 'wb') as w:
                w.setnchannels(1)
                w.setsampwidth(2)
                w.setframerate(44100)
                w.writeframes(b'\x00\x00' * 44100)
            files.append(wav_path)

        result = validator.validate_batch(files)

        assert result['total_files'] == 5
        assert result['throughput'] > 0  # Should have positive throughput
        assert len(result['results']) == 5

    def test_batch_validation_deduplicates_repeated_path(self, validator, temp_wav_file):
        """validate_batch indexa 'results' por str(filepath) — arquivos
        repetidos no batch produzem 1 entrada, não N. Isso é intencional:
        reaproveita o cache de validate_file() em vez de reprocessar o
        mesmo arquivo várias vezes. total_files continua refletindo o
        tamanho do batch de entrada (5), não o número de resultados
        únicos (1) — os dois números têm significados diferentes de
        propósito, não é uma inconsistência.
        """
        files = [temp_wav_file] * 5
        result = validator.validate_batch(files)

        assert result['total_files'] == 5
        assert len(result['results']) == 1
        assert str(temp_wav_file) in result['results']
    
    def test_convenience_function(self, validator, temp_wav_file):
        """Test convenience validation function."""
        result = validate_audio_input(temp_wav_file)
        assert result is True
    
    def test_memory_efficiency(self, validator, temp_wav_file):
        """Test memory usage under constraints."""
        import sys
        
        initial_memory = sys.getsizeof(validator.validation_cache)
        validator.validate_file(temp_wav_file)
        after_validation_memory = sys.getsizeof(validator.validation_cache)
        
        memory_increase = after_validation_memory - initial_memory
        assert memory_increase <= 1000  # Less than 1KB per cached result

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=packages.audio.validate", "--cov-report=term-missing"])
