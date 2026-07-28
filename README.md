<img width="404" height="79" alt="Screenshot 2026-07-28 101857" src="https://github.com/user-attachments/assets/993883d8-349f-4e49-b593-22ce191cb5d3" />

# TruthLens AI

TruthLens AI is a multimodal AI verification platform that detects misinformation, AI-generated media, and synthetic voices using multiple LLMs, computer vision, and speech analysis. It supports OpenAI GPT-4o and local Ollama models through a modular architecture.

## Features

- Multi-LLM Support
- GPT-4o + Ollama
- AI Image Detection
- AI Voice Detection
- Video Verification
- Chrome Extension
- Explainable Trust Score

## Tech Stack

Frontend:
- React
- TailwindCSS

Backend:
- FastAPI

LLMs:
- OpenAI GPT-4o
- Llama 3.2
- Gemma 3
- Mistral
- Phi-3

AI Models:
- Whisper
- Hugging Face Image Detector
- Hugging Face Audio Anti-Spoofing

## Architecture

GitHub automatically renders Mermaid diagrams. Here is the structure of the TruthLens AI platform:

```mermaid
graph TD
    Client[React Frontend / Chrome Extension] -->|HTTP / WebSockets| API[FastAPI Backend]
    API -->|Prompt & Verification| Adapt[Model Adapter / Verification Service]
    Adapt -->|Remote Analysis| OpenAI[OpenAI API GPT-4o]
    Adapt -->|Local Analysis| Ollama[Local Ollama Service]
    Adapt -->|Media Spoofing Detection| HF[Hugging Face Models Hub]
```


## Installation

### Clone

```bash
git clone https://github.com/OmSons30/TruthLens-AI.git
cd TruthLens-AI
```

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Chrome Extension

To load the Chrome Extension locally:

1. Open Google Chrome and navigate to `chrome://extensions/`.
2. Enable **Developer mode** using the toggle switch in the top-right corner.
3. Click the **Load unpacked** button in the top-left corner.
4. Select the `chrome-extension` folder from the root of the project.

### Ollama

```bash
ollama pull llama3.2
ollama pull gemma3
ollama pull mistral
```

Start Ollama:

```bash
ollama serve
```

### Environment Variables

Create `.env`

```env
OPENAI_API_KEY=xxxxxxxx
OLLAMA_URL=http://localhost:11434
```

## Usage

Run backend:

```bash
uvicorn main:app --reload
python main.py
```

Run frontend:

```bash
npm run dev
```

## Screenshots




## Future Improvements

- Browser Extension
- More LLMs
- RAG
- Better Deepfake Detection

## License

MIT
