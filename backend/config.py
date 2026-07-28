import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file relative to this file
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

class Settings:
    PROJECT_NAME: str = "TruthLens AI Backend"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    
    # OpenAI settings
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    
    # Ollama settings
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_LLAMA_MODEL: str = os.getenv("OLLAMA_LLAMA_MODEL", "llama3.1")
    OLLAMA_MISTRAL_MODEL: str = os.getenv("OLLAMA_MISTRAL_MODEL", "mistral")
    OLLAMA_GEMMA_MODEL: str = os.getenv("OLLAMA_GEMMA_MODEL", "gemma3")
    OLLAMA_DEEPSEEK_MODEL: str = os.getenv("OLLAMA_DEEPSEEK_MODEL", "deepseek-r1")
    
    # Hugging Face Settings
    HUGGINGFACE_API_KEY: str = os.getenv("HUGGINGFACE_API_KEY", "")

settings = Settings()
