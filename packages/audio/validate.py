# packages/audio/validate.py
"""
MELO Audio Engine - File Validation Module

Responsibilities:
    - Validate supported audio file formats  
    - Verify file existence, extension, and basic integrity
    - Ensure cross-platform compatibility (ARM64→AMD64)
    - Maintain 350MB RAM constraint compliance
    - Termux-compatible implementation
"""

import os
import sys
import time
from pathlib import Path
from typing import Union, List, Tuple
import wave  # Built-in, compatible with Termux
import struct

class AudioValidator:
    """Audio file validation engine with Termux compatibility."""
    
    SUPPORTED_FORMATS = {'.wav', '.flac', '.ogg', '.mp3', '.aac'}
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB limit
    
    def __init__(self):
        self.validation_cache = {}
        
    def validate_file(self, filepath: Union[str, Path]) -> Tuple[bool, str]:
        """
        Validate single audio file with comprehensive checks.
        
        Args:
            filepath: Path to audio file
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        path = Path(filepath)
        
        # Check cache first
        if str(path) in self.validation_cache:
            return self.validation_cache[str(path)]
            
        try:
            # File existence check
            if not path.exists():
                result = False, f"File does not exist: {path}"
                
            # Extension validation
            elif path.suffix.lower() not in self.SUPPORTED_FORMATS:
                result = False, f"Unsupported format: {path.suffix}"
                
            # Size validation
            elif path.stat().st_size > self.MAX_FILE_SIZE:
                result = False, f"File too large: {path.stat().st_size} bytes"
                
            # Basic integrity check using built-in wave module
            else:
                is_integrity_ok, integrity_msg = self._check_integrity(path)
                if is_integrity_ok:
                    result = True, "Valid"
                else:
                    result = False, integrity_msg
                    
        except Exception as e:
            result = False, f"Validation error: {str(e)}"
            
        self.validation_cache[str(path)] = result
        return result
    
    def _check_integrity(self, filepath: Path) -> Tuple[bool, str]:
        """Check audio file integrity using built-in wave module."""
        try:
            if filepath.suffix.lower() == '.wav':
                with wave.open(str(filepath), 'rb') as w:
                    frames = w.getnframes()
                    if frames == 0:
                        return False, "Empty audio file"
                    if w.getframerate() < 8000 or w.getframerate() > 192000:
                        return False, f"Invalid sample rate: {w.getframerate()}"
                    return True, "Integrity OK"
            else:
                # For non-WAV files, perform basic header check
                with open(filepath, 'rb') as f:
                    header = f.read(12)
                    if len(header) < 12:
                        return False, "File too small for audio"
                    # Basic format detection
                    if header[:4] in [b'RIFF', b'OggS', b'fLaC']:
                        return True, "Header OK"
                    else:
                        return False, "Invalid audio header"
        except wave.Error:
            return False, "Corrupted WAV file"
        except Exception as e:
            return False, f"Corrupted audio: {str(e)}"
    
    def validate_batch(self, filepaths: List[Union[str, Path]]) -> dict:
        """
        Validate multiple files with performance optimization.
        
        Returns:
            Dict with validation results and performance metrics
        """
        results = {}
        start_time = time.time()
        
        for filepath in filepaths:
            results[str(filepath)] = self.validate_file(filepath)
            
        execution_time = time.time() - start_time
        
        return {
            'results': results,
            'total_files': len(filepaths),
            'execution_time': execution_time,
            'throughput': len(filepaths) / execution_time if execution_time > 0 else 0
        }

def validate_audio_input(input_path: Union[str, Path]) -> bool:
    """Convenience function for single file validation."""
    validator = AudioValidator()
    is_valid, _ = validator.validate_file(input_path)
    return is_valid

if __name__ == "__main__":
    # Performance validation
    import time
    
    if len(sys.argv) != 2:
        print("Usage: python validate.py <audio_file>")
        sys.exit(1)
        
    validator = AudioValidator()
    filepath = sys.argv[1]
    
    start = time.time()
    is_valid, message = validator.validate_file(filepath)
    duration = time.time() - start
    
    print(f"Validation: {'PASS' if is_valid else 'FAIL'}")
    print(f"Message: {message}")
    print(f"Duration: {duration:.3f}s")
    print(f"Memory impact: ~{sys.getsizeof(validator.validation_cache)} bytes")
