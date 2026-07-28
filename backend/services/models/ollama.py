import base64
import json
import logging
from typing import List, Optional, Dict, Any, AsyncGenerator
import httpx
from services.models.base import BaseModelAdapter

logger = logging.getLogger("truthlens_ollama_adapter")

class OllamaAdapter(BaseModelAdapter):
    def __init__(self, base_url: str, model_name: str):
        self.base_url = base_url.rstrip("/")
        self.model_name = model_name

    async def _check_ollama_availability(self):
        """Quick check to see if local Ollama server is running."""
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                if response.status_code == 200:
                    # Let's check if the specific model is downloaded
                    models_data = response.json()
                    registered_models = [m["name"] for m in models_data.get("models", [])]
                    # Check prefix and exact matches
                    model_found = False
                    for m in registered_models:
                        if m == self.model_name or m.startswith(f"{self.model_name}:"):
                            model_found = True
                            break
                    if not model_found:
                        logger.warning(
                            f"Ollama model '{self.model_name}' was not detected in local list: {registered_models}. "
                            "It may fail if not pulled. Attempting invocation anyway."
                        )
                else:
                    raise Exception(f"Ollama returned status check {response.status_code}")
        except httpx.ConnectError:
            raise ValueError(
                f"Ollama is not running. Start Ollama and download the model with `ollama run {self.model_name}`. "
                f"Connection failed to {self.base_url}"
            )
        except Exception as e:
            logger.warning(f"Failed to check Ollama status: {e}")

    def _prepare_payload(self, prompt: str, files: Optional[List[Dict[str, Any]]] = None, stream: bool = False) -> Dict[str, Any]:
        images = []
        if files:
            for file_info in files:
                mime_type = file_info.get("mime_type", "")
                if mime_type.startswith("image/"):
                    raw_data = file_info.get("data")
                    if isinstance(raw_data, bytes):
                        b64_data = base64.b64encode(raw_data).decode("utf-8")
                    else:
                        b64_data = raw_data
                    
                    # Ollama expects raw base64 data without data:image/... url prefix
                    if "," in b64_data:
                        b64_data = b64_data.split(",")[1]
                    images.append(b64_data)

        message = {
            "role": "user",
            "content": prompt
        }
        if images:
            message["images"] = images

        return {
            "model": self.model_name,
            "messages": [message],
            "stream": stream,
            "options": {
                "temperature": 0.2
            }
        }

    async def generate(self, prompt: str, files: Optional[List[Dict[str, Any]]] = None) -> str:
        await self._check_ollama_availability()
        payload = self._prepare_payload(prompt, files, stream=False)
        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                if response.status_code != 200:
                    raise Exception(f"Ollama returned HTTP {response.status_code}: {response.text}")
                
                result = response.json()
                return result.get("message", {}).get("content", "")
        except httpx.TimeoutException:
            raise Exception("Ollama model execution timed out. The local model is taking too long to load or generate.")
        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            raise Exception(f"Failed to generate response using Ollama model ({self.model_name}): {str(e)}")

    async def stream_generate(self, prompt: str, files: Optional[List[Dict[str, Any]]] = None) -> AsyncGenerator[str, None]:
        await self._check_ollama_availability()
        payload = self._prepare_payload(prompt, files, stream=True)
        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/api/chat",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status_code != 200:
                        raise Exception(f"Ollama stream returned HTTP {response.status_code}")
                    
                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        try:
                            chunk_data = json.loads(line)
                            content = chunk_data.get("message", {}).get("content", "")
                            if content:
                                yield content
                            if chunk_data.get("done", False):
                                break
                        except json.JSONDecodeError:
                            continue
        except httpx.TimeoutException:
            raise Exception("Ollama stream connection connection timed out.")
        except Exception as e:
            logger.error(f"Ollama streaming failed: {e}")
            raise Exception(f"Ollama connection error during streaming: {str(e)}")
