import json
import logging
import re
from typing import Dict, Any
from schemas import VerificationRequest, VerificationResponse, TrustScoreDetails
from config import settings

logger = logging.getLogger("truthlens_pipeline")

SYSTEM_PROMPT = """
You are TruthLens AI, an industry-grade, highly precise semantic and visual fact-checking agent.
Your objective is to evaluate suspicious digital media (text claims, image forwards, screenshared articles, screenshots) with extreme precision.

Please conduct an exhaustive evaluation in a single step matching these precise dimensions:
1. Claim Extraction: Extract the exact core claim being made. Be objective, specific, and clear.
2. Multimodal OCR: If a screenshot is provided, extract all relevant overlay text with maximum spatial precision, noting formatting.
3. Media Integrity (AI Generation / Manipulation): Look for clues of:
   - Visual Manipulation (photoshop overlays, alignment mismatch, altered fonts, fake forward counters, layout fabrications).
   - AI Generation traits (blurred details, plastic skin textures, gibberish background text, warped borders, floating pixels, lighting inconsistencies).
   - If it is synthetic or warning flags exist, classify as AI-generated and describe the exact clues in 'media_analysis'.
4. Factuality Check: Corroborate details against verified facts resource databases, checking for misinformation templates (phishing links, fake government schemes, clickbait).
5. Scored Trust Index:
   - 0-25: Likely False (High Risk). Obvious scam or fabricated context.
   - 26-50: Suspicious (Medium-High Risk). AI generated, modified, or highly misleading context.
   - 51-75: Needs Verification (Medium Risk). Missing context, unverified claims.
   - 76-100: Likely Authentic (Low Risk). Standard public notices or verified news.
6. Actionable Advice: Provide concrete, direct, and authoritative steps (e.g. "Do not forward. Phishing link detected; delete the message immediately.").

You MUST return strictly valid JSON matching the following schema structure:
{
  "claim": "string (the objective core claim extracted)",
  "score": integer (0 to 100),
  "category": "Likely False | Suspicious | Needs Verification | Likely Authentic",
  "risk_level": "HIGH | MEDIUM | LOW",
  "reasons": ["string (exact reason 1)", "string (exact reason 2)"],
  "recommendation": "string (direct, sharp actionable advice)",
  "media_analysis": "string (detailed synthesis of AI generation checks and visual manipulation findings)",
  "fact_check_notes": "string (supporting factuality notes and verification databases references)"
}
"""

def mock_fallback_analysis(text: str, source: str) -> VerificationResponse:
    """Intelligent fallback when OpenAI API key is missing or calls are rate limited."""
    text_lower = text.lower() if text else ""
    
    # Simple heuristic checks for mock demonstration
    if any(k in text_lower for k in ["subsidy", "free", "50,000", "50000", "lottery", "click link", "forward to", "modi scheme", "government giving"]):
        score = 18
        category = "Likely False"
        risk_level = "HIGH"
        reasons = [
            "No official government portal or trusted news agency has reported this scheme.",
            "Contains typical urgency indicators commonly found in viral forwarding scams.",
            "Context mismatch detected: official subsidies are never distributed via messaging apps."
        ]
        recommendation = "Do not forward this message or click any attached links."
        claim = f"Government or authority offering unauthorized financial payout or subsidy."
    elif any(k in text_lower for k in ["urgent", "breaking news", "nasa", "alien", "miracle", "cure"]):
        score = 38
        category = "Suspicious"
        risk_level = "MEDIUM"
        reasons = [
            "Sensationalized headlines lacking primary source verification.",
            "Unverified scientific or medical claims circulating without peer review.",
            "Potential out-of-context image or quote usage."
        ]
        recommendation = "Cross-check with credible fact-checking websites before sharing."
        claim = "Sensational claims circulating on social channels."
    else:
        score = 82
        category = "Likely Authentic"
        risk_level = "LOW"
        reasons = [
            "Information aligns with verified public announcements.",
            "No signs of artificial manipulation or deceptive framing detected."
        ]
        recommendation = "Information appears consistent, but always stay vigilant."
        claim = text[:100] if text else "Verified digital announcement"

    return VerificationResponse(
        claim=claim,
        trust_score=TrustScoreDetails(score=score, category=category, risk_level=risk_level),
        reasons=reasons,
        recommendation=recommendation,
        detailed_analysis={
            "ocr_extracted_text": text or "Sample screen payload processed",
            "source_app": source,
            "engine": "Fallback Heuristic Verification Engine"
        }
    )

async def run_verification_pipeline(request: VerificationRequest) -> VerificationResponse:
    text_content = request.raw_text or ""
    
    # If no text and image base64 provided, simulate OCR extraction
    if not text_content and request.image_base64:
        text_content = "Government giving ₹50,000 subsidy to citizens under emergency relief fund. Click here to register."
    
    if not text_content:
        text_content = "Suspicious forwarded announcement with claim of free rewards."

    # Check if OpenAI API Key is available
    if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY.strip() == "" or settings.OPENAI_API_KEY == "your_openai_api_key_here":
        logger.info("Using fallback mock engine (OpenAI API key not configured).")
        return mock_fallback_analysis(text_content, request.source_app or "WhatsApp")

    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Prepare multimodal content array for vision models
        user_content = []
        
        if request.raw_text:
            user_content.append({
                "type": "text",
                "text": f"Source App Context: {request.source_app or 'Unknown'}\nText claim content to analyze:\n\"{request.raw_text}\""
            })
            
        if request.image_base64:
            user_content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{request.image_base64}"
                }
            })
            user_content.append({
                "type": "text",
                "text": "Analyze the screenshot above. If no raw text was specified, derive the claim from OCR extraction of this screenshot. Carefully analyze aesthetic and visual clues to assess whether it shows visual manipulation or AI generation traits, and report them in 'media_analysis'."
            })
            
        if not user_content:
            user_content.append({
                "type": "text",
                "text": "Suspicious generic claim announcement."
            })

        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,  # gpt-4o-mini supports vision inputs
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content}
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
            max_tokens=600
        )

        content = response.choices[0].message.content
        data = json.loads(content)

        return VerificationResponse(
            claim=data.get("claim", request.raw_text or "Screenshotted claim"),
            trust_score=TrustScoreDetails(
                score=data.get("score", 50),
                category=data.get("category", "Needs Verification"),
                risk_level=data.get("risk_level", "MEDIUM")
            ),
            reasons=data.get("reasons", ["Analysis completed."]),
            recommendation=data.get("recommendation", "Verify before forwarding."),
            detailed_analysis={
                "ocr_extracted_text": request.raw_text or data.get("claim", "N/A"),
                "source_app": request.source_app,
                "media_analysis": data.get("media_analysis", "N/A"),
                "fact_check_notes": data.get("fact_check_notes", "N/A"),
                "engine": f"OpenAI Multimodal ({settings.OPENAI_MODEL})"
            }
        )
    except Exception as e:
        print(f"DEBUG ERROR calling OpenAI API: {e}")
        logger.error(f"Error calling OpenAI API: {e}. Falling back to heuristic model.")
        return mock_fallback_analysis(text_content, request.source_app or "WhatsApp")
