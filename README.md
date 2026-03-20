# Career Bot Starter

This project is a starter RAG-based employer Q&A bot built with:
- FastAPI
- OpenAI Responses API
- OpenAI file search tool
- OpenAI vector stores

## 1) Create a virtual environment

### macOS / Linux
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Windows PowerShell
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

## 2) Install dependencies
```bash
pip install -r requirements.txt
```

## 3) Set environment variables
Copy `.env.example` to `.env` and fill in your API key.

## 4) Upload docs and create a vector store
From the project root:
```bash
python upload_docs.py
```

That script will print a vector store ID. Put it into your `.env` as `OPENAI_VECTOR_STORE_ID`.

## 5) Run the API
```bash
uvicorn app:app --reload
```

## 6) Test it
Health check:
```bash
curl http://127.0.0.1:8000/health
```

Chat example:
```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "Tell me about Justin\'s work history."}'
```

## Suggested next steps
- Add a simple React or Next.js frontend
- Tighten the markdown files with exact dates, titles, and accomplishments
- Add metadata filtering later if you want company- or topic-specific retrieval
- Add a public-safe review pass to every source file
