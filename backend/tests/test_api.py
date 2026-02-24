"""
Smoke tests for the FastAPI application.
Uses httpx AsyncClient — no real network, no LLM calls.
"""
import io
import sys
import os
import pytest
from httpx import AsyncClient, ASGITransport

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Patch env before importing app so GRADIENT_API_KEY is set
os.environ.setdefault("GRADIENT_API_KEY", "test-key-for-ci")

from main import app  # noqa: E402


@pytest.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


# ── Health / root ─────────────────────────────────────────────────────────── #

async def test_health(client):
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json()["ok"] is True


async def test_root(client):
    r = await client.get("/")
    assert r.status_code == 200
    data = r.json()
    assert "service" in data
    assert data["platform"] == "DigitalOcean Gradient™ AI"


# ── Upload ────────────────────────────────────────────────────────────────── #

CSV_BYTES = b"product,units,revenue\nWidget,10,1000\nGadget,5,2000\nDoohickey,20,500\n"


async def test_upload_csv_success(client):
    r = await client.post(
        "/upload",
        files={"file": ("sales.csv", io.BytesIO(CSV_BYTES), "text/csv")},
    )
    assert r.status_code == 200
    data = r.json()
    assert "session_id" in data
    assert data["row_count"] == 3
    assert data["col_count"] == 3
    assert data["filename"] == "sales.csv"


async def test_upload_non_csv_rejected(client):
    r = await client.post(
        "/upload",
        files={"file": ("data.xlsx", io.BytesIO(b"fake"), "application/octet-stream")},
    )
    assert r.status_code == 400


async def test_upload_empty_file_rejected(client):
    r = await client.post(
        "/upload",
        files={"file": ("empty.csv", io.BytesIO(b""), "text/csv")},
    )
    assert r.status_code == 400


# ── Session management ────────────────────────────────────────────────────── #

async def test_query_unknown_session_404(client):
    r = await client.post(
        "/query",
        json={"session_id": "nonexistent-session-id", "question": "What is the total revenue?"},
    )
    assert r.status_code == 404


async def test_delete_session(client):
    # Upload first
    r = await client.post(
        "/upload",
        files={"file": ("sales.csv", io.BytesIO(CSV_BYTES), "text/csv")},
    )
    session_id = r.json()["session_id"]

    # Delete
    r2 = await client.delete(f"/session/{session_id}")
    assert r2.status_code == 200
    assert r2.json()["deleted"] == session_id

    # Now query should 404
    r3 = await client.post(
        "/query",
        json={"session_id": session_id, "question": "How many rows?"},
    )
    assert r3.status_code == 404


async def test_delete_nonexistent_session_ok(client):
    """Deleting a non-existent session should not error."""
    r = await client.delete("/session/does-not-exist")
    assert r.status_code == 200
