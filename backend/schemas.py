from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class VerificationRequest(BaseModel):
    raw_text: Optional[str] = None
    image_base64: Optional[str] = None
    source_app: Optional[str] = "WhatsApp"

class TrustScoreDetails(BaseModel):
    score: int
    category: str
    risk_level: str  # "HIGH", "MEDIUM", "LOW"

class VerificationResponse(BaseModel):
    claim: str
    trust_score: TrustScoreDetails
    reasons: List[str]
    recommendation: str
    detailed_analysis: Dict[str, Any]


# ── Audio / Voice Verification Schemas ──────────────────────────────

class AudioVerificationRequest(BaseModel):
    audio_base64: str
    source_app: Optional[str] = "Voice Upload"

class VoiceAuthenticityDetails(BaseModel):
    score: int                   # 0-100, higher = more likely authentic
    is_synthetic: bool           # True if AI-generated / cloned voice detected
    confidence: str              # "HIGH", "MEDIUM", "LOW"
    analysis: str                # Human-readable explanation

class AudioVerificationResponse(BaseModel):
    transcript: str
    voice_authenticity: VoiceAuthenticityDetails
    content_verification: VerificationResponse


# ── Bot / Multimodal Detector Schemas ───────────────────────────────

class DetectorOutput(BaseModel):
    ai_probability: float
    confidence: str
    metadata: Dict[str, Any]

class ChatResponse(BaseModel):
    detector_result: Optional[DetectorOutput] = None
    explanation: str
    model: str
