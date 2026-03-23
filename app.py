import os
from dotenv import load_dotenv
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from pydantic import BaseModel, Field
from openai import OpenAI

load_dotenv()

# OpenAI's file search tool is available in the Responses API,
# and vector stores are used as the backing retrieval index.
# See official docs:
# https://developers.openai.com/api/docs/guides/tools-file-search/
# https://developers.openai.com/api/docs/guides/retrieval/

APP_TITLE = "Career Bot API"
MODEL = os.getenv("OPENAI_MODEL", "gpt-5")
VECTOR_STORE_ID = os.getenv("OPENAI_VECTOR_STORE_ID", "")
ALLOWED_ORIGIN = os.getenv("ALLOWED_ORIGIN", "*")

SYSTEM_PROMPT = """
You are an employer-facing career profile assistant for Justin Gapper.

Use the retrieved knowledge base to answer questions about Justin's work history,
leadership experience, strengths, and career themes.

Rules:
- Use only supported information from the knowledge base.
- Do not invent job titles, dates, company details, metrics, project names, or outcomes.
- If the answer is not supported by the documents, say that clearly.
- Keep answers concise, polished, and recruiter-friendly.
- Prefer a confident but factual tone.
- Avoid confidential, proprietary, or overly specific internal details.
- Where helpful, synthesize across multiple retrieved passages.
""".strip()

client = OpenAI()
app = FastAPI(title=APP_TITLE)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[ALLOWED_ORIGIN] if ALLOWED_ORIGIN != "*" else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    max_num_results: int = Field(default=5, ge=1, le=10)


class ChatResponse(BaseModel):
    answer: str
    citations: list[dict[str, Any]] = []


class HealthResponse(BaseModel):
    ok: bool
    model: str
    vector_store_id_present: bool


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        ok=True,
        model=MODEL,
        vector_store_id_present=bool(VECTOR_STORE_ID),
    )

@app.get("/")
def home():
    return FileResponse(Path("index.html"))


@app.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest) -> ChatResponse:
    if not VECTOR_STORE_ID:
        raise HTTPException(
            status_code=500,
            detail="OPENAI_VECTOR_STORE_ID is not configured.",
        )

    try:
        response = client.responses.create(
            model=MODEL,
            instructions=SYSTEM_PROMPT,
            input=payload.question,
            tools=[
                {
                    "type": "file_search",
                    "vector_store_ids": [VECTOR_STORE_ID],
                    "max_num_results": payload.max_num_results,
                }
            ],
            include=["file_search_call.results"],
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"OpenAI API error: {exc}") from exc

    answer = getattr(response, "output_text", "").strip()
    citations = extract_file_search_results(response)

    if not answer:
        answer = "I couldn't generate an answer from the current knowledge base."

    return ChatResponse(answer=answer, citations=citations)


def extract_file_search_results(response: Any) -> list[dict[str, Any]]:
    """
    Best-effort extraction of file search hits from the Responses API object.
    The exact shape may evolve over time, so this function stays defensive.
    """
    citations: list[dict[str, Any]] = []

    output = getattr(response, "output", None)
    if not output:
        return citations

    for item in output:
        if getattr(item, "type", None) != "file_search_call":
            continue

        results = getattr(item, "results", None) or []
        for result in results:
            filename = getattr(result, "filename", None) or getattr(result, "file_name", None)
            score = getattr(result, "score", None)
            text = getattr(result, "text", None)
            citations.append(
                {
                    "filename": filename,
                    "score": score,
                    "snippet": (text[:300] + "...") if isinstance(text, str) and len(text) > 300 else text,
                }
            )

    return citations


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
