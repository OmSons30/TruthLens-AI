"""
Test the audio verification pipeline with a programmatically generated WAV file.
"""
import asyncio
import base64
import struct
import math

from schemas import AudioVerificationRequest
from agents.audio_pipeline import run_audio_verification_pipeline


def generate_test_wav(duration_s: float = 2.0, sample_rate: int = 16000, freq: float = 440.0) -> bytes:
    """Generate a minimal WAV file (sine wave) for testing."""
    num_samples = int(sample_rate * duration_s)
    # Generate sine wave samples
    samples = []
    for i in range(num_samples):
        t = i / sample_rate
        value = int(32767 * 0.5 * math.sin(2 * math.pi * freq * t))
        samples.append(struct.pack('<h', value))
    
    raw_data = b''.join(samples)
    data_size = len(raw_data)
    
    # Build WAV header
    wav = bytearray()
    wav.extend(b'RIFF')
    wav.extend(struct.pack('<I', 36 + data_size))
    wav.extend(b'WAVE')
    wav.extend(b'fmt ')
    wav.extend(struct.pack('<I', 16))       # chunk size
    wav.extend(struct.pack('<H', 1))        # PCM
    wav.extend(struct.pack('<H', 1))        # mono
    wav.extend(struct.pack('<I', sample_rate))
    wav.extend(struct.pack('<I', sample_rate * 2))  # byte rate
    wav.extend(struct.pack('<H', 2))        # block align
    wav.extend(struct.pack('<H', 16))       # bits per sample
    wav.extend(b'data')
    wav.extend(struct.pack('<I', data_size))
    wav.extend(raw_data)
    
    return bytes(wav)


async def test():
    print("=" * 60)
    print("Testing TruthLens Audio Verification Pipeline")
    print("=" * 60)
    
    # Generate a test WAV
    wav_bytes = generate_test_wav(duration_s=1.5)
    audio_b64 = base64.b64encode(wav_bytes).decode('utf-8')
    
    print(f"Generated test WAV: {len(wav_bytes)} bytes")
    print(f"Base64 length: {len(audio_b64)} chars")
    
    # Create request
    req = AudioVerificationRequest(
        audio_base64=audio_b64,
        source_app="Test"
    )
    
    # Run pipeline
    print("\nRunning audio verification pipeline...")
    res = await run_audio_verification_pipeline(req)
    
    print("\n--- RESULTS ---")
    print(f"Transcript: {res.transcript[:200]}...")
    print(f"\nVoice Authenticity Score: {res.voice_authenticity.score}/100")
    print(f"Is Synthetic: {res.voice_authenticity.is_synthetic}")
    print(f"Confidence: {res.voice_authenticity.confidence}")
    print(f"Analysis: {res.voice_authenticity.analysis}")
    print(f"\nContent Trust Score: {res.content_verification.trust_score.score}")
    print(f"Category: {res.content_verification.trust_score.category}")
    print(f"Risk Level: {res.content_verification.trust_score.risk_level}")
    print(f"Claim: {res.content_verification.claim}")
    print(f"Recommendation: {res.content_verification.recommendation}")
    
    # Basic assertions
    assert res.transcript, "Transcript should not be empty"
    assert 0 <= res.voice_authenticity.score <= 100, "Voice score should be 0-100"
    assert res.voice_authenticity.confidence in ("HIGH", "MEDIUM", "LOW")
    assert res.content_verification.trust_score.score >= 0
    
    print("\n✓ All assertions passed!")


if __name__ == "__main__":
    asyncio.run(test())
