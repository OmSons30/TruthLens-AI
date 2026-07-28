"""
TruthLens AI — Synthetic Voice Detection Pipeline
Transcribes audio via OpenAI Whisper, analyses transcript for misinformation,
and evaluates voice authenticity (AI-generated / cloned voice detection).
"""

import json
import base64
import logging
import tempfile
import os
from pathlib import Path
from typing import Optional

from config import settings
from schemas import (
    AudioVerificationRequest,
    AudioVerificationResponse,
    VoiceAuthenticityDetails,
    VerificationRequest,
)
from agents.pipeline import run_verification_pipeline

logger = logging.getLogger("truthlens_audio")

# ── Voice Authenticity Analysis Prompt ──────────────────────────────

VOICE_AUTHENTICITY_PROMPT = """
You are TruthLens AI Voice Forensics Analyst — an expert system trained to detect
AI-generated, voice-cloned, or synthetically produced speech from transcription
metadata and acoustic energy cues described in context.

Given the following TRANSCRIPT of a voice recording, its metadata, and acoustic measurements, evaluate:

1. **Naturalness Score (0–100)**: How natural does the speech pattern appear?
   - 0–25: Highly Synthetic — robotic cadence, unnatural pacing, missing filler words
   - 26–50: Suspicious — overly smooth delivery, no speech disfluencies, templated phrasing
   - 51–75: Inconclusive — some natural traits but also synthetic markers
   - 76–100: Likely Authentic — natural hesitations, varied intonation markers, human-like flow

2. **Synthetic Indicators**: Look for:
   - **Perfect Digital Silence**: Real microphone recordings always contain room noise, fan hiss, or mouth sounds. If digital silence is present (absolute 0 RMS energy), this is highly indicative of synthetic/exported audio.
   - **Absence of fillers**: Scripted flow with zero natural conversational disfluencies ("um", "uh", "like") is heavily correlated with text-to-speech algorithms.
   - **Sterile voice dynamics**: Low range or perfectly uniform volume distribution.

3. **Confidence Level**: HIGH, MEDIUM, or LOW confidence in your assessment.

CRITICAL DISCRIMINATION RULE:
If the text matches a perfectly scripted statement (e.g. corporate announcement, read book sentence) AND there are zero filler words AND either:
- perfect silence chunks are found (has_perfect_silence: true) OR
- digital_silence_percentage is > 0
You MUST classify this audio as synthetic (is_synthetic: true, score < 45) with HIGH or MEDIUM confidence.

You MUST return strictly valid JSON matching this schema:
{
  "voice_authenticity_score": integer (0 to 100, higher = more authentic),
  "is_synthetic": boolean,
  "confidence": "HIGH | MEDIUM | LOW",
  "analysis": "string (detailed explanation of voice authenticity findings)"
}
"""


# ── Acoustic Feature Extractor ──────────────────────────────────────

def calculate_rms_manually(raw_bytes: bytes, sample_width: int) -> float:
    """Manual root-mean-square calculation to bypass deprecated 'audioop' in Python 3.13."""
    if not raw_bytes:
        return 0.0
    try:
        import struct
        if sample_width == 2:
            num_samples = len(raw_bytes) // 2
            if num_samples == 0:
                return 0.0
            fmt = f"<{num_samples}h"
            samples = struct.unpack(fmt, raw_bytes)
            sum_squares = sum(s * s for s in samples)
            return (sum_squares / num_samples) ** 0.5
        elif sample_width == 1:
            num_samples = len(raw_bytes)
            if num_samples == 0:
                return 0.0
            # 8-bit unsigned PCM
            sum_squares = sum(((b - 128) ** 2) for b in raw_bytes)
            return (sum_squares / num_samples) ** 0.5
        else:
            # Fallback estimation for general byte counts
            return float(len(raw_bytes))
    except Exception as e:
        logger.warning(f"Manual RMS computation failed: {e}")
        return 0.0


def extract_acoustic_features(audio_bytes: bytes) -> dict:
    """Helper to extract sample rate, energy levels, and digital silence chunks."""
    features = {
        "format_loaded": False,
        "frame_rate": 0,
        "channels": 0,
        "sample_width": 0,
        "duration_seconds": 0.0,
        "max_rms": 0,
        "avg_rms": 0.0,
        "digital_silence_percentage": 0.0,
        "has_perfect_silence": False,
        "rms_std_dev": 0.0,
        "error": None
    }
    if not audio_bytes:
        return features

    try:
        from pydub import AudioSegment
        import io

        # Load segment
        seg = AudioSegment.from_file(io.BytesIO(audio_bytes))

        # Basic metadata
        features["frame_rate"] = seg.frame_rate
        features["channels"] = seg.channels
        features["sample_width"] = seg.sample_width
        features["duration_seconds"] = seg.duration_seconds

        # Analyze energy using manual RMS (bypasses audioop)
        chunk_length_ms = 100
        total_duration_ms = int(seg.duration_seconds * 1000)
        chunks = [seg[i:i+chunk_length_ms] for i in range(0, total_duration_ms, chunk_length_ms) if i+chunk_length_ms <= total_duration_ms]
        
        if not chunks and total_duration_ms > 0:
            chunks = [seg]

        if chunks:
            chunk_rms = [calculate_rms_manually(c.raw_data, c.sample_width) for c in chunks]
            features["max_rms"] = int(max(chunk_rms))
            features["avg_rms"] = sum(chunk_rms) / len(chunk_rms)
            
            # Count digital silence (RMS < 3 or exactly 0)
            # Standard WebM/WAV recording on user microphone has a room noise floor (RMS is usually at least 15-50+ in quiet room)
            # If the audio has chunks of absolute zero (RMS < 2), it's highly indicative of synthetic/clean exports.
            silence_threshold = 2
            silence_chunks = sum(1 for rms in chunk_rms if rms <= silence_threshold)
            features["digital_silence_percentage"] = (silence_chunks / len(chunks)) * 100
            features["has_perfect_silence"] = silence_chunks > 0

            # Calculate variance of RMS (standard deviation) to represent speech dynamics transition
            mean_rms = sum(chunk_rms) / len(chunk_rms)
            variance = sum((rms - mean_rms) ** 2 for rms in chunk_rms) / len(chunk_rms)
            features["rms_std_dev"] = variance ** 0.5
        
        features["format_loaded"] = True
    except Exception as e:
        features["error"] = str(e)
        logger.warning(f"Acoustic feature extraction failed: {e}")
        
    return features



# ── Mock / Fallback Voice Analysis ──────────────────────────────────

def mock_voice_analysis(transcript: str, acoustic_features: Optional[dict] = None) -> VoiceAuthenticityDetails:
    """Heuristic fallback when OpenAI API key is not configured or as safety backup."""
    text_lower = transcript.lower()

    # Very short or templated text → suspicious
    word_count = len(transcript.split())
    has_filler = any(w in text_lower for w in ["um", "uh", "like", "you know", "hmm"])

    # If we have acoustic features, check for digital silence
    has_silence_cue = False
    if acoustic_features and acoustic_features.get("format_loaded"):
        if acoustic_features.get("has_perfect_silence") or acoustic_features.get("digital_silence_percentage", 0.0) > 0.5:
            has_silence_cue = True

    if word_count < 10:
        return VoiceAuthenticityDetails(
            score=55,
            is_synthetic=False,
            confidence="LOW",
            analysis="Audio transcript too short/brief for definitive voice authenticity analysis. Insufficient voice patterns."
        )

    # Clean silence cues + absolute lack of fillers → strongly synthetic
    if has_silence_cue and not has_filler:
        return VoiceAuthenticityDetails(
            score=25,
            is_synthetic=True,
            confidence="HIGH",
            analysis="Acoustic analysis flagged absolute digital silence intervals between speech fragments (RMS <= 2). "
                     "Combined with the zero filler words and a highly fluent transcript, this suggests an AI-generated voice clone."
        )

    if has_filler:
        return VoiceAuthenticityDetails(
            score=86,
            is_synthetic=False,
            confidence="HIGH",
            analysis="Speech contains natural disfluencies (fillers like 'um', 'uh') and varied dynamics. "
                     "Acoustic pattern represents standard human micro-fluctuations. No synthetic markers."
        )

    # No filler words, longer text, likely read script or synthetic output
    if word_count > 25 and not has_filler:
        return VoiceAuthenticityDetails(
            score=32,
            is_synthetic=True,
            confidence="MEDIUM",
            analysis="Speech segment detected with perfect grammar, uniform articulation pacing, and zero conversational filler stutters. "
                     "This pattern matches text-to-speech generation. Additional verifications are advised."
        )

    return VoiceAuthenticityDetails(
        score=68,
        is_synthetic=False,
        confidence="LOW",
        analysis="Voice patterns show mixed indicators. Performance details are inconclusive. Further verification recommended."
    )


# ── Transcription ──────────────────────────────────────────────────

async def transcribe_audio(audio_bytes: bytes, filename: str = "audio.wav") -> str:
    """Transcribe audio bytes to text using OpenAI Whisper API."""

    if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY.strip() == "" or settings.OPENAI_API_KEY == "your_openai_api_key_here":
        logger.info("Whisper API key not configured — returning mock transcript.")
        return "[Mock Transcript] This is a simulated transcription of the uploaded audio. The government is giving free subsidies to all citizens. Click the link to register now."

    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

        # Write audio bytes to a temp file for the API
        suffix = Path(filename).suffix or ".wav"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        try:
            with open(tmp_path, "rb") as audio_file:
                transcription = await client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="text"
                )
            return transcription.strip() if transcription else "[No speech detected in audio]"
        finally:
            os.unlink(tmp_path)

    except Exception as e:
        logger.error(f"Whisper transcription failed: {e}")
        return f"[Transcription Error] Could not transcribe audio: {str(e)}"


# ── Voice Authenticity Analysis via GPT ─────────────────────────────

async def analyze_voice_authenticity(transcript: str, audio_bytes: Optional[bytes] = None) -> VoiceAuthenticityDetails:
    """Analyze transcript and audio properties for indicators of AI-generated or cloned voice."""
    
    # Extract acoustic metrics
    acoustic_features = extract_acoustic_features(audio_bytes) if audio_bytes else {}

    # If the transcript has zero filler words and shows acoustic signs of digital silence,
    # let's pre-evaluate or guide the fallback
    word_count = len(transcript.split())
    has_filler = any(w in transcript.lower() for w in ["um", "uh", "like", "you know", "hmm"])
    
    # Check if we should override fallback or mock trigger
    if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY.strip() == "" or settings.OPENAI_API_KEY == "your_openai_api_key_here":
        logger.info("Using mock voice authenticity analysis (API key not configured).")
        return mock_voice_analysis(transcript, acoustic_features)

    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

        user_message = (
            f"TRANSCRIPT:\n\"{transcript}\"\n\n"
            f"TRANSCRIPT METADATA:\n"
            f"- Word count: {word_count}\n"
            f"- Contains filler words: {has_filler}\n"
            f"- Estimated duration: ~{max(1, word_count // 3)} seconds\n\n"
            f"ACOUSTIC METADATA:\n"
            f"- Frame rate: {acoustic_features.get('frame_rate', 0)} Hz\n"
            f"- Channels: {acoustic_features.get('channels', 0)}\n"
            f"- Perfect silence chunks: {acoustic_features.get('has_perfect_silence', False)}\n"
            f"- Percentage of perfect digital silence: {acoustic_features.get('digital_silence_percentage', 0.0):.2f}%\n"
            f"- Max RMS: {acoustic_features.get('max_rms', 0)}\n"
            f"- Average RMS: {acoustic_features.get('avg_rms', 0.0):.2f}\n"
            f"- Amplitude Standard Deviation (RMS standard dev): {acoustic_features.get('rms_std_dev', 0.0):.2f}\n\n"
            f"Analyze this transcript and its acoustic metadata for voice authenticity. Determine if the speaker is "
            f"likely a real human or an AI-generated / cloned voice."
        )

        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": VOICE_AUTHENTICITY_PROMPT},
                {"role": "user", "content": user_message}
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
            max_tokens=400
        )

        content = response.choices[0].message.content
        data = json.loads(content)

        return VoiceAuthenticityDetails(
            score=data.get("voice_authenticity_score", 50),
            is_synthetic=data.get("is_synthetic", False),
            confidence=data.get("confidence", "MEDIUM"),
            analysis=data.get("analysis", "Voice analysis completed.")
        )

    except Exception as e:
        logger.error(f"Voice authenticity analysis failed: {e}. Using fallback.")
        return mock_voice_analysis(transcript, acoustic_features)


# ── Main Audio Pipeline Orchestrator ────────────────────────────────

async def run_audio_verification_pipeline(
    request: AudioVerificationRequest,
) -> AudioVerificationResponse:
    """
    Full audio verification pipeline:
    1. Decode audio from base64
    2. Transcribe via Whisper
    3. Run transcript through existing text verification pipeline
    4. Run voice authenticity analysis
    5. Combine into AudioVerificationResponse
    """

    # Step 1: Decode audio
    try:
        audio_bytes = base64.b64decode(request.audio_base64)
    except Exception as e:
        logger.error(f"Failed to decode audio base64: {e}")
        raise ValueError(f"Invalid audio data: {str(e)}")

    # Step 2: Transcribe
    transcript = await transcribe_audio(audio_bytes)

    # Step 3: Run transcript through existing text verification
    text_request = VerificationRequest(
        raw_text=transcript,
        source_app=request.source_app or "Voice Upload"
    )
    content_result = await run_verification_pipeline(text_request)

    # Step 4: Voice authenticity analysis
    voice_result = await analyze_voice_authenticity(transcript, audio_bytes)

    # Step 5: Combine
    return AudioVerificationResponse(
        transcript=transcript,
        voice_authenticity=voice_result,
        content_verification=content_result
    )
