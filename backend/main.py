"""FastAPI backend for the K3 university-policy chatbot demo.

Wraps the Lab 7 knowledge base (ingest.build_knowledge_base + EmbeddingStore)
with a citation-aware chat agent (backend/chat_agent.py) and exposes it over
HTTP for the React/Vite frontend in frontend/.

Run:
    .\\.venv\\Scripts\\python.exe -m uvicorn backend.main:app --reload --port 8000

Requires OPENAI_API_KEY in .env (repo root) for both embeddings and chat
completions. Falls back to the mock embedder (semantically meaningless, but
keeps the server usable offline) if EMBEDDING_PROVIDER is unset/unavailable.
"""
from __future__ import annotations

import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

load_dotenv(ROOT / ".env")

from ingest import build_knowledge_base  # noqa: E402
from main import DEFAULT_DATA_DIR, _select_embedder  # noqa: E402
from src.chunking import RecursiveChunker  # noqa: E402

from backend.chat_agent import CitingChatAgent  # noqa: E402

DATA_DIR = os.getenv("LAB_DATA_DIR", DEFAULT_DATA_DIR)
CHAT_MODEL = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")

state: dict[str, Any] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    embedder = _select_embedder()
    backend_name = getattr(embedder, "_backend_name", embedder.__class__.__name__)
    store = build_knowledge_base(
        str(ROOT / DATA_DIR),
        embedding_fn=embedder,
        chunker=RecursiveChunker(chunk_size=500),
    )

    client = None
    if os.getenv("OPENAI_API_KEY"):
        from openai import OpenAI

        client = OpenAI()

    state["store"] = store
    state["agent"] = CitingChatAgent(store=store, client=client, chat_model=CHAT_MODEL) if client else None
    state["embedding_backend"] = backend_name
    print(f"[backend] embedding backend: {backend_name}")
    print(f"[backend] loaded {store.get_collection_size()} chunks from {DATA_DIR}")
    print(f"[backend] chat model: {CHAT_MODEL} ({'ready' if client else 'DISABLED - no OPENAI_API_KEY'})")

    yield
    state.clear()


app = FastAPI(title="VinUni K3 Policy Assistant API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1, le=10)
    audience: str | None = Field(default=None, description='Optional metadata filter, e.g. "student"')


class CitationOut(BaseModel):
    index: int
    doc_id: str
    title: str
    source_url: str
    category: str | None = None
    audience: str | None = None
    score: float
    snippet: str


class ChatResponseOut(BaseModel):
    answer: str
    citations: list[CitationOut]


@app.get("/api/health")
def health() -> dict[str, Any]:
    store = state.get("store")
    return {
        "status": "ok",
        "embedding_backend": state.get("embedding_backend"),
        "collection_size": store.get_collection_size() if store else 0,
        "chat_enabled": state.get("agent") is not None,
    }


@app.post("/api/chat", response_model=ChatResponseOut)
def chat(request: ChatRequest) -> ChatResponseOut:
    agent: CitingChatAgent | None = state.get("agent")
    if agent is None:
        raise HTTPException(
            status_code=503,
            detail="Chat is disabled: no OPENAI_API_KEY configured on the server.",
        )

    metadata_filter = {"audience": request.audience} if request.audience else None
    try:
        response = agent.ask(request.message, top_k=request.top_k, metadata_filter=metadata_filter)
    except Exception as error:
        # The frontend should receive a useful, stable response even if an
        # external embedding/chat provider has a temporary 5xx outage.
        print(f"[backend] chat request degraded: {error}")
        return ChatResponseOut(
            answer=(
                "Dịch vụ AI đang tạm thời gián đoạn nên chưa thể phân tích câu hỏi. "
                "Vui lòng thử lại sau ít phút."
            ),
            citations=[],
        )
    return ChatResponseOut(**response.to_dict())
