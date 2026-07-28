import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from services.detectors import detect_image_integrity, detect_audio_spoofing, detect_video_deepfake

async def test_detectors():
    print("=" * 60)
    print("Testing Media Integrity Detectors and Heuristic Fallbacks")
    print("=" * 60)
    
    # 1. Test image detector mockup
    img_data = b"fake-jpeg-data"
    img_res = await detect_image_integrity(img_data, "fake_midjourney_render.jpg")
    print(f"✓ Image scan: Probability={img_res['ai_probability']}, Confidence={img_res['confidence']}, Source={img_res['metadata']['source']}")
    assert img_res['ai_probability'] > 0.8 # triggered by filename "fake"
    
    # 2. Test audio spoofing detector mockup
    aud_res = await detect_audio_spoofing(b"fake-wav-data", "normal_recording.wav")
    print(f"✓ Audio scan: Probability={aud_res['ai_probability']}, Confidence={aud_res['confidence']}, Source={aud_res['metadata']['source']}")
    
    # 3. Test video deepfake detector mockup
    vid_res = await detect_video_deepfake(b"fake-mp4-data", "deepfake_swap.mp4")
    print(f"✓ Video scan: Probability={vid_res['ai_probability']}, Confidence={vid_res['confidence']}, Source={vid_res['metadata']['source']}")
    assert vid_res['ai_probability'] > 0.9 # triggered by filename "deepfake"
    
    print("\n✓ Media integrity detectors initialized successfully!")

if __name__ == "__main__":
    asyncio.run(test_detectors())
