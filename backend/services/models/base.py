from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, AsyncGenerator

class BaseModelAdapter(ABC):
    @abstractmethod
    async def generate(self, prompt: str, files: Optional[List[Dict[str, Any]]] = None) -> str:
        """
        Generate a complete response for a prompt and optional list of media file dictionaries.
        Each file dict should have: {"name": str, "data": bytes, "mime_type": str}
        """
        pass

    @abstractmethod
    async def stream_generate(self, prompt: str, files: Optional[List[Dict[str, Any]]] = None) -> AsyncGenerator[str, None]:
        """
        Stream response chunks for a prompt and optional list of media file dictionaries.
        Each file dict should have: {"name": str, "data": bytes, "mime_type": str}
        """
        pass
