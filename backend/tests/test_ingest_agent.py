"""
Tests for IngestAgent — CSV parsing, column profiling, schema summary.
Offline only: no network, no LLM.
"""
import io
import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agents.ingest_agent import IngestAgent


def _csv(content: str) -> bytes:
    return content.strip().encode()


@pytest.fixture
def agent():
    return IngestAgent()


# ── Basic parsing ────────────────────────────────────────────────────────────

def test_basic_csv_parses(agent):
    csv = _csv("""
name,revenue,region
Alice,1000,North
Bob,2000,South
Carol,1500,East
""")
    profile = agent.ingest(csv, "sales.csv")
    assert profile["filename"] == "sales.csv"
    assert profile["row_count"] == 3
    assert profile["col_count"] == 3
    assert len(profile["columns"]) == 3
    assert len(profile["sample_rows"]) == 3


def test_column_types_inferred(agent):
    csv = _csv("""
product,units,price
Widget,10,9.99
Gadget,5,19.99
Doohickey,20,4.99
""")
    profile = agent.ingest(csv, "products.csv")
    col_map = {c["name"]: c for c in profile["columns"]}

    assert col_map["product"]["dtype"] == "categorical"
    assert col_map["units"]["dtype"] == "numeric"
    assert col_map["price"]["dtype"] == "numeric"
    assert col_map["units"]["mean"] is not None
    assert col_map["price"]["min"] == pytest.approx(4.99, rel=1e-3)
    assert col_map["price"]["max"] == pytest.approx(19.99, rel=1e-3)


def test_nullable_detected(agent):
    csv = _csv("""
id,value
1,100
2,
3,300
""")
    profile = agent.ingest(csv, "nulls.csv")
    col_map = {c["name"]: c for c in profile["columns"]}
    assert col_map["value"]["nullable"] is True
    assert col_map["value"]["null_count"] == 1


def test_schema_summary_contains_filename(agent):
    csv = _csv("a,b\n1,2\n3,4")
    profile = agent.ingest(csv, "mydata.csv")
    assert "mydata.csv" in profile["schema_summary"]
    assert "Rows:" in profile["schema_summary"]


def test_empty_file_raises(agent):
    with pytest.raises(ValueError):
        agent.ingest(b"", "empty.csv")


def test_non_csv_bytes_raises(agent):
    with pytest.raises(ValueError):
        agent.ingest(b"\x00\x01\x02\x03", "binary.csv")


def test_large_column_is_text(agent):
    """A column with many unique string values should be typed 'text'."""
    rows = "\n".join(f"user_{i},val_{i}" for i in range(200))
    csv = _csv(f"user_id,value\n{rows}")
    profile = agent.ingest(csv, "big.csv")
    col_map = {c["name"]: c for c in profile["columns"]}
    assert col_map["user_id"]["dtype"] == "text"
