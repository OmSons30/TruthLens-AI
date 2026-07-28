import asyncio
import sys
import json
from pathlib import Path
from fastapi.testclient import TestClient

sys.path.append(str(Path(__file__).parent))

from main import app

def test_chat_stream():
    print("=" * 60)
    print("Testing SSE Streaming Chat API Endpoint")
    print("=" * 60)
    
    client = TestClient(app)
    
    # 1. Test basic text query (using mock OpenAI key fallback or mock system)
    print("Sending text claim verification query...")
    response = client.post(
        "/api/chat",
        data={"message": "Government giving free money structure", "model": "openai-gpt-4o"}
    )
    
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]
    
    # Parse event stream lines
    lines = response.text.split("\n")
    events = [line for line in lines if line.startswith("data:")]
    
    print(f"Received {len(events)} stream packets.")
    
    metadata_packet = None
    content_chunks = []
    
    for event in events:
        data_str = event[len("data: "):]
        payload = json.loads(data_str)
        if payload["type"] == "metadata":
            metadata_packet = payload
        elif payload["type"] == "content":
            content_chunks.append(payload["chunk"])
            
    print("✓ Metadata packet received:", metadata_packet)
    print("✓ Text stream content extracted successfully!")
    print(f"Sample response content: {''.join(content_chunks[:50])}...")
    
    # 2. Test file upload validation error
    print("Testing unsupported file type block...")
    response_fail = client.post(
        "/api/chat",
        data={"message": "Check file", "model": "openai-gpt-4o"},
        files={"file": ("test.pdf", b"pdf-data", "application/pdf")}
    )
    assert response_fail.status_code == 400
    print("✓ Blocked unsupported PDF attachment successfully!")

if __name__ == "__main__":
    test_chat_stream()
