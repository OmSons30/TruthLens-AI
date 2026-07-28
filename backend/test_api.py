import asyncio
from schemas import VerificationRequest
from agents.pipeline import run_verification_pipeline

async def test():
    print("Testing TruthLens Verification Pipeline...")
    req = VerificationRequest(
        raw_text="⚠ URGENT: Government giving ₹50,000 subsidy under Direct Relief Scheme to all account holders! Register now at http://bit.ly/fake-subsidy",
        source_app="WhatsApp"
    )
    res = await run_verification_pipeline(req)
    print("Claim:", res.claim)
    print("Trust Score:", res.trust_score.score, "-", res.trust_score.category)
    print("Reasons:", res.reasons)
    print("Recommendation:", res.recommendation)

if __name__ == "__main__":
    asyncio.run(test())
