import asyncio
import sys
from pathlib import Path

# Add backend directory to path if needed to run directly
sys.path.append(str(Path(__file__).parent))

from services.models.router import get_model_adapter
from services.models.base import BaseModelAdapter

async def test_router():
    print("=" * 60)
    print("Testing Model Adapters and Router")
    print("=" * 60)
    
    # 1. Test Router Selection
    openai_adapter = get_model_adapter("openai-gpt-4o")
    print(f"✓ Retrieved OpenAI adapter: {type(openai_adapter)}")
    assert isinstance(openai_adapter, BaseModelAdapter)
    
    llama_adapter = get_model_adapter("ollama-llama3.1")
    print(f"✓ Retrieved Ollama Llama adapter: {type(llama_adapter)}")
    assert isinstance(llama_adapter, BaseModelAdapter)
    
    deepseek_adapter = get_model_adapter("ollama-deepseek-r1")
    print(f"✓ Retrieved Ollama DeepSeek adapter: {type(deepseek_adapter)}")
    
    # 2. Assert model mapping
    assert openai_adapter.model_name == "gpt-4o-mini" # default set in config.py
    assert llama_adapter.model_name == "llama3.1"
    assert deepseek_adapter.model_name == "deepseek-r1"
    
    print("\n✓ Router and model mappings look correct!")

if __name__ == "__main__":
    asyncio.run(test_router())
