import base64
import json
import logging
from typing import Optional
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from config import settings
from schemas import (
    VerificationRequest, VerificationResponse,
    AudioVerificationRequest, AudioVerificationResponse,
)
from agents.pipeline import run_verification_pipeline
from agents.audio_pipeline import run_audio_verification_pipeline, transcribe_audio

# Chat service imports
from services.models.router import get_model_adapter
from services.detectors import detect_image_integrity, detect_audio_spoofing, detect_video_deepfake

logger = logging.getLogger("truthlens_main")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="TruthLens AI Backend API - Shazam for Misinformation"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {
        "status": "online",
        "app": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "model": settings.OPENAI_MODEL
    }

@app.post("/api/verify", response_model=VerificationResponse)
async def verify_content(request: VerificationRequest):
    try:
        result = await run_verification_pipeline(request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Audio Verification Endpoints ────────────────────────────────────

@app.post("/api/verify-audio", response_model=AudioVerificationResponse)
async def verify_audio(request: AudioVerificationRequest):
    """Verify audio from base64 encoded data (JSON body)."""
    try:
        result = await run_audio_verification_pipeline(request)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/verify-audio-upload", response_model=AudioVerificationResponse)
async def verify_audio_upload(
    file: UploadFile = File(...),
    source_app: str = Form("Voice Upload"),
):
    """Verify audio uploaded as multipart/form-data file."""
    try:
        audio_bytes = await file.read()
        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
        request = AudioVerificationRequest(
            audio_base64=audio_b64,
            source_app=source_app,
        )
        result = await run_audio_verification_pipeline(request)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Chatbot Endpoint (Multi-Model & Media Verification) ───────────────

@app.post("/api/chat")
async def chat_endpoint(
    message: Optional[str] = Form(None),
    model: str = Form("openai-gpt-4o"),
    file: Optional[UploadFile] = File(None)
):
    """
    Modular Multi-Model Verification Chatbot Endpoint.
    Streams back analysis explanation via SSE (Server-Sent Events).
    Pre-processes files via Hugging Face detectors and feeds output to LLM.
    """
    # 1. Parse optional file uploads
    file_bytes = None
    file_name = ""
    file_type = ""
    detector_result = None
    transcript = None
    
    if file:
        file_name = file.filename
        file_type = file.content_type or ""
        # Check for unsupported file formats
        allowed_prefixes = ("image/", "audio/", "video/")
        if not file_type.startswith(allowed_prefixes):
            # Check by extension if content-type is generic octet-stream
            ext = file_name.split(".")[-1].lower()
            if ext in ["jpg", "jpeg", "png", "webp"]:
                file_type = "image/jpeg"
            elif ext in ["wav", "mp3", "m4a", "ogg", "webm", "aac"]:
                file_type = "audio/wav"
            elif ext in ["mp4", "avi", "mov", "mkv", "webm-video"]:
                file_type = "video/mp4"
            else:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Unsupported file format '{file_name}'. Must be an image, audio, or video file."
                )
                
        try:
            file_bytes = await file.read()
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to read upload: {str(e)}")

    # 2. Run media integrity detectors
    if file_bytes:
        try:
            if file_type.startswith("image/"):
                detector_result = await detect_image_integrity(file_bytes, file_name)
            elif file_type.startswith("audio/"):
                # First get transcription for audio file
                trans_result = await transcribe_audio(file_bytes, file_name)
                # Filter out mock errors
                if "[Transcription Error]" in trans_result:
                    transcript = f"Audio transcription failed or was offline ({trans_result})."
                else:
                    transcript = trans_result
                detector_result = await detect_audio_spoofing(file_bytes, file_name)
            elif file_type.startswith("video/"):
                detector_result = await detect_video_deepfake(file_bytes, file_name)
        except Exception as e:
            logger.error(f"Detector scanning execution failure: {e}")
            # Do not throw, fallback to safe mock details
            detector_result = {
                "ai_probability": 0.5,
                "confidence": "LOW",
                "metadata": {"error": f"Detector execution failed: {str(e)}"}
            }

    # 3. Create context prompt for selected LLM adapter
    base_prompt = ""
    if detector_result:
        # File attached prompt
        if file_type.startswith("image/"):
            base_prompt = (
                "You are TruthLens AI, an expert multimodal verification chatbot. "
                "The user has uploaded an image for integrity verification.\n"
                f"User original query: \"{message or ''}\"\n\n"
                "Media integrity scanner outputs:\n"
                f"- Image AI Probability (Artificial generation score): {detector_result['ai_probability']:.2f}\n"
                f"- Detection Confidence: {detector_result['confidence']}\n"
                f"- Scan metadata: {detector_result['metadata']}\n\n"
                "Please explain the verification results in a beautiful, authoritative, and direct manner: "
                "Interpret the AI probability, explain whether visual manipulation or AI generation markers exist, "
                "and give concrete recommendations (e.g. should they forward or delete it?)."
            )
        elif file_type.startswith("audio/"):
            base_prompt = (
                "You are TruthLens AI, an expert multimodal verification chatbot. "
                "The user has uploaded a speech recording/voice memo for integrity verification.\n"
                f"User original query: \"{message or ''}\"\n\n"
                f"Voice transcript (transcribed via Whisper): \"{transcript or '[Unrecognized/Silence]'}\"\n\n"
                "Acoustic authenticity pipeline outputs:\n"
                f"- Voice Spoof/Synthesis Probability: {detector_result['ai_probability']:.2f}\n"
                f"- Detection Confidence: {detector_result['confidence']}\n"
                f"- Audio metadata: {detector_result['metadata']}\n\n"
                "Please evaluate both the voice authenticity and contents of this transcript: "
                "Highlight the likelihood of voice cloning (spoof), explain why, fact-check the statements in the transcript, "
                "and give direct actionable verification recommendations."
            )
        elif file_type.startswith("video/"):
            base_prompt = (
                "You are TruthLens AI, an expert multimodal verification chatbot. "
                "The user has uploaded a video clip for integrity verification.\n"
                f"User original query: \"{message or ''}\"\n\n"
                "Temporal deepfake detection scanner outputs:\n"
                f"- Deepfake Probability: {detector_result['ai_probability']:.2f}\n"
                f"- Detection Confidence: {detector_result['confidence']}\n"
                f"- Video scan metadata: {detector_result['metadata']}\n\n"
                "Please explain the video deepfake risk: "
                "Interpret the deepfake score, discuss typical digital artifacts like mouth misalignment or face warping "
                "in this context, and advise the user how to approach the integrity of this video."
            )
    else:
        # Standard claim query (no file upload)
        if not message or message.strip() == "":
            raise HTTPException(status_code=400, detail="Verification request requires a message or a media file.")
            
        base_prompt = (
            "You are TruthLens AI, an expert Multi-Model verification chatbot. "
            f"The user wishes to verify this text claim/message:\n\"{message}\"\n\n"
            "Evaluate this claim's credibility, check for potential scams, phishing links, or misinformation, "
            "and lay out reasons, trust score, and actionable steps to verify or discredit it."
        )

    # 4. Stream response using SSE
    async def sse_stream_generator():
        # First send the metadata/detector result
        meta_payload = {
            "type": "metadata",
            "detector_result": detector_result,
            "transcript": transcript,
            "model": model
        }
        yield f"data: {json.dumps(meta_payload)}\n\n"
        
        # Instantiate the selected model adapter
        try:
            adapter = get_model_adapter(model)
            
            # Format files for adapters that can ingest it directly (e.g. OpenAI Vision)
            adapter_files = None
            if file_bytes and file_type.startswith("image/"):
                adapter_files = [{
                    "name": file_name,
                    "data": file_bytes,
                    "mime_type": file_type
                }]
            
            # Stream token chunks
            async for chunk in adapter.stream_generate(base_prompt, adapter_files):
                yield f"data: {json.dumps({'type': 'content', 'chunk': chunk})}\n\n"
                
        except ValueError as e:
            # e.g. Ollama missing / key missing
            logger.error(f"Configuration or connection error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'detail': str(e)})}\n\n"
        except Exception as e:
            logger.error(f"Adapter streaming failed: {e}")
            yield f"data: {json.dumps({'type': 'error', 'detail': f'Error streaming from model {model}: {str(e)}'})}\n\n"
            
        # Send closing done flag
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(sse_stream_generator(), media_type="text/event-stream")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
