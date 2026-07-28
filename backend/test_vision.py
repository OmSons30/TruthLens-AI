import asyncio
import base64
from pathlib import Path
from schemas import VerificationRequest
from agents.pipeline import run_verification_pipeline

async def test():
    print("Testing Vision Analysis...")
    image_path = Path(__file__).parent.parent / "frontend" / "src" / "assets" / "hero.png"
    if not image_path.exists():
        print(f"Error: image {image_path} does not exist.")
        return
        
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
        
    req = VerificationRequest(
        raw_text=None,
        image_base64=encoded_string,
        source_app="WhatsApp"
    )
    
    res = await run_verification_pipeline(req)
    print("----- RESULT -----")
    print("Claim:", res.claim)
    print("Score:", res.trust_score.score)
    print("Category:", res.trust_score.category)
    print("Reasons:", res.reasons)
    print("Media Analysis:", res.detailed_analysis.get("media_analysis"))
    print("Engine:", res.detailed_analysis.get("engine"))

if __name__ == "__main__":
    asyncio.run(test())
