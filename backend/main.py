"""
Gradient Fisherman — FastAPI backend
SMB Data Assistant powered by DigitalOcean Gradient™ AI + Claude Sonnet 4.6
"""

from __future__ import annotations

import io
import os
import uuid
from typing import Any

import pandas as pd
from cachetools import TTLCache
from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from openai import AsyncOpenAI
from pydantic import BaseModel

from agents import IngestAgent, QueryAgent, VizAgent

load_dotenv()

# ── Config ─────────────────────────────────────────────────────────────────── #

GRADIENT_API_KEY  = os.getenv("GRADIENT_API_KEY", "")
GRADIENT_BASE_URL = os.getenv("GRADIENT_BASE_URL", "https://inference.do-ai.run/v1")
GRADIENT_MODEL    = os.getenv("GRADIENT_MODEL", "claude-sonnet-4-6")

# ── App ────────────────────────────────────────────────────────────────────── #

app = FastAPI(
    title="Gradient Fisherman API",
    description="SMB Data Assistant — DigitalOcean Gradient™ AI Hackathon",
    version="1.0.0",
    docs_url="/docs",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Singleton agents ───────────────────────────────────────────────────────── #

ingest_agent = IngestAgent()
viz_agent    = VizAgent()

# ── Session store: TTLCache (max 50 sessions, 30-min TTL) ─────────────────── #
# Caps memory at 50 concurrent sessions; each auto-expires after 30 minutes.
# Sessions are in-process only — lost on restart (acceptable for demo).
# For production: replace with Redis or a persistent store.

sessions: TTLCache = TTLCache(maxsize=50, ttl=1800)  # 1800 s = 30 min

# ── Helpers ────────────────────────────────────────────────────────────────── #

def _gradient_client() -> AsyncOpenAI:
    if not GRADIENT_API_KEY:
        raise HTTPException(
            status_code=503,
            detail=(
                "GRADIENT_API_KEY not set. "
                "Add your DigitalOcean Gradient Model Access Key to the environment."
            ),
        )
    return AsyncOpenAI(api_key=GRADIENT_API_KEY, base_url=GRADIENT_BASE_URL)

# ── Schemas ────────────────────────────────────────────────────────────────── #

class QueryRequest(BaseModel):
    session_id: str
    question: str

class QueryResponse(BaseModel):
    session_id: str
    question: str
    answer_summary: str
    pandas_code: str
    result_type: str
    result_data: Any
    chart: dict
    error: str | None

class UploadResponse(BaseModel):
    session_id: str
    filename: str
    row_count: int
    col_count: int
    columns: list[dict]
    sample_rows: list[dict]
    schema_summary: str

# ── Routes ─────────────────────────────────────────────────────────────────── #

@app.get("/")
async def root():
    return {
        "service": "Gradient Fisherman API",
        "model":   GRADIENT_MODEL,
        "platform": "DigitalOcean Gradient™ AI",
        "status":  "ready" if GRADIENT_API_KEY else "needs_api_key",
    }

@app.get("/health")
async def health():
    return {"ok": True}


@app.post("/upload", response_model=UploadResponse)
async def upload_csv(file: UploadFile = File(...)):
    """Upload a CSV. Returns session_id + data profile."""
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(400, "Only CSV files are supported.")

    contents = await file.read()
    if len(contents) == 0:
        raise HTTPException(400, "File is empty.")
    if len(contents) > 50 * 1024 * 1024:
        raise HTTPException(413, "File too large (max 50 MB).")

    try:
        profile = ingest_agent.ingest(contents, file.filename)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc

    df = pd.read_csv(io.BytesIO(contents), nrows=100_000)
    session_id = str(uuid.uuid4())
    sessions[session_id] = {"profile": profile, "df": df}

    return UploadResponse(
        session_id=session_id,
        filename=profile["filename"],
        row_count=profile["row_count"],
        col_count=profile["col_count"],
        columns=profile["columns"],
        sample_rows=profile["sample_rows"],
        schema_summary=profile["schema_summary"],
    )


@app.post("/query", response_model=QueryResponse)
async def query_data(req: QueryRequest):
    """Ask a natural-language question about the uploaded dataset."""
    session = sessions.get(req.session_id)
    if not session:
        raise HTTPException(404, "Session not found. Upload a CSV first.")

    client      = _gradient_client()
    query_agent = QueryAgent(client=client, model=GRADIENT_MODEL)
    profile     = session["profile"]
    df: pd.DataFrame = session["df"]

    result = await query_agent.query(
        question=req.question,
        df=df,
        schema_summary=profile["schema_summary"],
    )

    chart = viz_agent.generate(
        result_data=result["result_data"],
        result_type=result["result_type"],
        suggested_chart=result["suggested_chart"],
        chart_x_col=result["chart_x_col"],
        chart_y_col=result["chart_y_col"],
        answer_summary=result["answer_summary"],
    )

    return QueryResponse(
        session_id=req.session_id,
        question=req.question,
        answer_summary=result["answer_summary"],
        pandas_code=result["pandas_code"],
        result_type=result["result_type"],
        result_data=result["result_data"],
        chart=chart,
        error=result["error"],
    )


@app.delete("/session/{session_id}")
async def delete_session(session_id: str):
    sessions.pop(session_id, None)
    return {"deleted": session_id}


@app.get("/models")
async def list_models():
    """List available Gradient AI models."""
    client = _gradient_client()
    try:
        models = await client.models.list()
        return {"models": [m.id for m in models.data]}
    except Exception as exc:
        raise HTTPException(502, f"Cannot reach Gradient AI: {exc}") from exc
