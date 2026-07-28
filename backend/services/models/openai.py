import base64
import logging
from typing import List, Optional, Dict, Any, AsyncGenerator
from openai import AsyncOpenAI, APIError
from services.models.base import BaseModelAdapter

logger = logging.getLogger("truthlens_openai_adapter")

class OpenAIAdapter(BaseModelAdapter):
    def __init__(self, api_key: str, model_name: str = "gpt-4o"):
        self.api_key = api_key
        self.model_name = model_name
        self.client = None
        if api_key and api_key.strip() != "" and api_key != "your_openai_api_key_here":
            self.client = AsyncOpenAI(api_key=api_key)

    def _check_client(self):
        if not self.client:
            raise ValueError(
                "OpenAI API key is missing or not configured. "
                "Please configure a valid OPENAI_API_KEY in your .env or backend config."
            )

    def _prepare_messages(self, prompt: str, files: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        user_content = []
        
        # Add text prompt first
        user_content.append({
            "type": "text",
            "text": prompt
        })
        
        # Add images if present
        if files:
            for file_info in files:
                mime_type = file_info.get("mime_type", "")
                if mime_type.startswith("image/"):
                    # The data comes in as bytes. Let's base64 encode it.
                    raw_data = file_info.get("data")
                    if isinstance(raw_data, bytes):
                        b64_data = base64.b64encode(raw_data).decode("utf-8")
                    else:
                        b64_data = raw_data
                    
                    user_content.append({
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{b64_data}"
                        }
                    })

        return [
            {"role": "user", "content": user_content}
        ]

    async def generate(self, prompt: str, files: Optional[List[Dict[str, Any]]] = None) -> str:
        self._check_client()
        messages = self._prepare_messages(prompt, files)
        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.2,
                max_tokens=1000
            )
            return response.choices[0].message.content or ""
        except APIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise Exception(f"OpenAI service error: {e.message}")
        except Exception as e:
            logger.error(f"OpenAI generation failed: {e}")
            raise Exception(f"Failed to generate response using OpenAI: {str(e)}")

    async def stream_generate(self, prompt: str, files: Optional[List[Dict[str, Any]]] = None) -> AsyncGenerator[str, None]:
        self._check_client()
        messages = self._prepare_messages(prompt, files)
        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.2,
                max_tokens=1000,
                stream=True
            )
            async for chunk in response:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if delta and delta.content:
                        yield delta.content
        except APIError as e:
            logger.error(f"OpenAI API streaming error: {e}")
            raise Exception(f"OpenAI streaming error: {e.message}")
        except Exception as e:
            logger.error(f"OpenAI streaming failed: {e}")
            raise Exception(f"OpenAI streaming connection error: {str(e)}")
