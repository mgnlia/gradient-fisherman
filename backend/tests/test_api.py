"""Integration tests for FastAPI endpoints (no LLM calls)."""

import pytest
from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def client():
    return TestClient(app)


CSV_BYTES = (
    b"product,category,units,revenue\n"
    b"Widget A,Electronics,10,500.00\n"
    b"Widget B,Clothing,5,150.00\n"
    b"Gadget X,Electronics,2,1200.00\n"
)


def test_root(client):
    r = client.get("/")
    assert r.status_code == 200
    data = r.json()
    assert data["service"] == "Gradient Fisherman API"


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_upload_csv(client):
    r = client.post(
        "/upload",
        files={"file": ("sales.csv", CSV_BYTES, "text/csv")},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["row_count"] == 3
    assert data["col_count"] == 4
    assert "session_id" in data
    assert len(data["columns"]) == 4


def test_upload_non_csv(client):
    r = client.post(
        "/upload",
        files={"file": ("data.xlsx", b"fake", "application/octet-stream")},
    )
    assert r.status_code == 400


def test_query_no_session(client):
    r = client.post(
        "/query",
        json={"session_id": "nonexistent-id", "question": "How many rows?"},
    )
    assert r.status_code == 404


def test_delete_session(client):
    # upload first
    r = client.post(
        "/upload",
        files={"file": ("s.csv", CSV_BYTES, "text/csv")},
    )
    session_id = r.json()["session_id"]
    # delete
    r2 = client.delete(f"/session/{session_id}")
    assert r2.status_code == 200
    # now query should 404
    r3 = client.post(
        "/query",
        json={"session_id": session_id, "question": "anything"},
    )
    assert r3.status_code == 404
