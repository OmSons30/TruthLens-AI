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
1. Dashboard for content verification
   <img width="1871" height="1076" alt="Screenshot 2026-07-28 101104" src="https://github.com/user-attachments/assets/5d7d3ee7-2466-4276-b336-56662d4bb4b8" />
*Features*   
-Deepfake detection: includes AI synthetic image verification.
-includes fake news detection using text verification.(uses openAi)
-Screen capture option

2. AI synthetic Audio verification.
   <img width="1587" height="852" alt="Screenshot 2026-07-28 101144" src="https://github.com/user-attachments/assets/442b829d-1dfa-4595-8c72-a59fe9fb6d22" />

3. Multimodal Chatbot for personalized verification.
   <img width="1423" height="1024" alt="Screenshot 2026-07-28 101359" src="https://github.com/user-attachments/assets/758a1d29-c367-4283-976b-94179136b786" />
   <img width="1423" height="1024" alt="Screenshot 2026-07-28 101359" src="https://github.com/user-attachments/assets/1324d0ff-463e-4747-8e0d-4701ce1b5d04" />
> trust score provided by the model.
   <img width="412" height="314" alt="Screenshot 2026-07-28 101510" src="https://github.com/user-attachments/assets/eae59b2b-1c09-4933-b945-460ad509dfbd" />

4. Extension for flexibility of user.
   <img width="1129" height="966" alt="image" src="https://github.com/user-attachments/assets/a83050b4-f424-4a39-b071-bb7c4dba39a8" />







## Future Improvements

- Browser Extension
- More LLMs
- RAG
- Better Deepfake Detection

## License

MIT
