"""
Audio Processing Utilities for Gemini Live Agent.

Provides helper functions for converting, resampling, normalizing, and chunking
PCM Int16 audio data flowing between the WebSocket client and the Google ADK runner.
"""

import struct
import math
import logging

try:
    import audioop  # Removed in Python 3.13, using audioop-lts package if installed
except ImportError:
    audioop = None

try:
    import numpy as np
    from scipy import signal
except ImportError:
    np = None
    signal = None

logger = logging.getLogger(__name__)

MICROPHONE_SAMPLE_RATE = 16000
AGENT_SAMPLE_RATE = 24000
BYTES_PER_SAMPLE = 2  # Int16

def pcm_to_bytes(audio_data: list[int]) -> bytes:
    """
    Convert a list of Int16 samples to raw bytes (little-endian).
    
    Args:
        audio_data: List of integer samples.
        
    Returns:
        Raw bytes representing the PCM audio.
    """
    try:
        # '<h' means little-endian short (int16)
        format_string = f"<{len(audio_data)}h"
        return struct.pack(format_string, *audio_data)
    except Exception as e:
        logger.error(f"Error converting pcm_data to bytes: {e}")
        return b""

def bytes_to_pcm(raw: bytes) -> list[int]:
    """
    Convert raw bytes back to Int16 sample list.
    
    Args:
        raw: Raw bytes representing PCM audio.
        
    Returns:
        List of integer samples.
    """
    try:
        if not raw or len(raw) % BYTES_PER_SAMPLE != 0:
            logger.warning("Invalid byte length for PCM conversion.")
            # Pad or truncate if absolutely necessary, but generally best to drop or handle gracefully
            padding = len(raw) % BYTES_PER_SAMPLE
            if padding:
                raw = raw[:-padding]

        format_string = f"<{len(raw) // BYTES_PER_SAMPLE}h"
        samples = struct.unpack(format_string, raw)
        return list(samples)
    except Exception as e:
        logger.error(f"Error converting bytes to pcm_data: {e}")
        return []

def resample_pcm(pcm_bytes: bytes, from_rate: int, to_rate: int) -> bytes:
    """
    Resample PCM audio from one sample rate to another.
    Tries audioop first, then scipy. Returns original if neither available.
    
    Args:
        pcm_bytes: Original raw PCM bytes.
        from_rate: Input sample rate (e.g., 16000).
        to_rate: Target sample rate (e.g., 24000).
        
    Returns:
        Resampled raw PCM bytes.
    """
    if from_rate == to_rate:
        return pcm_bytes

    # Attempt audioop first
    if audioop:
        try:
            # ratecv format: (data, sample_width, channels, in_rate, out_rate, state)
            resampled, _ = audioop.ratecv(pcm_bytes, BYTES_PER_SAMPLE, 1, from_rate, to_rate, None)
            return resampled
        except Exception as e:
            logger.warning(f"audioop ratecv failed: {e}. Falling back...")
    
    logger.warning("No audio resampling libraries (audioop) available. Returning original audio.")
    return pcm_bytes

def normalize_audio(pcm_bytes: bytes, target_peak: float = 0.8) -> bytes:
    """
    Normalize audio volume to target peak level.
    
    Args:
        pcm_bytes: Raw PCM bytes.
        target_peak: Target peak amplitude as a float [0.0, 1.0].
        
    Returns:
        Normalized raw PCM bytes.
    """
    try:
        samples = bytes_to_pcm(pcm_bytes)
        if not samples:
            return b""
            
        max_amplitude = float(max(abs(s) for s in samples))
        if max_amplitude == 0:
            return pcm_bytes
            
        # Int16 max value is 32767
        target_amplitude = 32767.0 * max(0.0, min(1.0, target_peak))
        gain = target_amplitude / max_amplitude
        
        # Avoid applying gain if it's already close
        if math.isclose(gain, 1.0, rel_tol=0.01):
            return pcm_bytes
            
        normalized_samples = [int(s * gain) for s in samples]
        # Clamp to Int16 limits
        normalized_samples = [max(-32768, min(32767, s)) for s in normalized_samples]
        
        return pcm_to_bytes(normalized_samples)
    except Exception as e:
        logger.error(f"Error normalizing audio: {e}")
        return pcm_bytes

def detect_silence(pcm_bytes: bytes, threshold: int = 500) -> bool:
    """
    Returns True if the audio chunk is below silence threshold.
    
    Args:
        pcm_bytes: Raw PCM bytes.
        threshold: Amplitude threshold below which audio is considered silent.
        
    Returns:
        True if silent, False otherwise.
    """
    try:
        if audioop:
            rms = audioop.rms(pcm_bytes, BYTES_PER_SAMPLE)
            return rms < threshold
        else:
            # Manual fallback
            samples = bytes_to_pcm(pcm_bytes)
            if not samples:
                return True
            rms = math.sqrt(sum(s*s for s in samples) / len(samples))
            return rms < threshold
    except Exception as e:
        logger.error(f"Error detecting silence: {e}")
        return False

def chunk_audio(pcm_bytes: bytes, chunk_ms: int = 100, sample_rate: int = 16000) -> list[bytes]:
    """
    Split a long PCM buffer into fixed-size chunks.
    
    Args:
        pcm_bytes: Raw PCM bytes.
        chunk_ms: Size of each chunk in milliseconds.
        sample_rate: Sample rate of the audio (default 16000).
        
    Returns:
        List of byte chunks.
    """
    try:
        samples_per_chunk = int(sample_rate * (chunk_ms / 1000.0))
        bytes_per_chunk = samples_per_chunk * BYTES_PER_SAMPLE
        
        chunks = []
        for i in range(0, len(pcm_bytes), bytes_per_chunk):
            chunk = pcm_bytes[i:i + bytes_per_chunk]
            # Optionally, you could drop the last chunk if it's inherently smaller, 
            # but keeping it is usually preferred to avoid dataloss.
            chunks.append(chunk)
            
        return chunks
    except Exception as e:
        logger.error(f"Error chunking audio: {e}")
        return [pcm_bytes]

def merge_audio_chunks(chunks: list[bytes]) -> bytes:
    """
    Merge multiple PCM byte chunks into one buffer.
    
    Args:
        chunks: List of byte chunks.
        
    Returns:
        Single merged byte buffer.
    """
    try:
        return b"".join(chunks)
    except Exception as e:
        logger.error(f"Error merging audio chunks: {e}")
        return b""
