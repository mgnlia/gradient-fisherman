"""Tests for IngestAgent."""

import io
import pytest
from agents.ingest_agent import IngestAgent


CSV_SALES = b"""date,product,category,units,revenue
2024-01-01,Widget A,Electronics,10,500.00
2024-01-02,Widget B,Clothing,5,150.00
2024-01-03,Widget A,Electronics,8,400.00
2024-01-04,Gadget X,Electronics,2,1200.00
2024-01-05,Widget B,Clothing,12,360.00
"""

CSV_MINIMAL = b"a,b\n1,2\n3,4\n"

CSV_MISSING = b"name,score\nAlice,90\nBob,\nCharlie,85\n"


@pytest.fixture
def agent():
    return IngestAgent()


def test_basic_parse(agent):
    profile = agent.ingest(CSV_SALES, "sales.csv")
    assert profile["row_count"] == 5
    assert profile["col_count"] == 5
    assert profile["filename"] == "sales.csv"


def test_column_types(agent):
    profile = agent.ingest(CSV_SALES, "sales.csv")
    cols = {c["name"]: c for c in profile["columns"]}

    assert cols["units"]["dtype"] == "numeric"
    assert cols["revenue"]["dtype"] == "numeric"
    assert cols["category"]["dtype"] == "categorical"
    assert cols["product"]["dtype"] == "categorical"
    # date should be parsed as datetime
    assert cols["date"]["dtype"] == "datetime"


def test_numeric_stats(agent):
    profile = agent.ingest(CSV_SALES, "sales.csv")
    cols = {c["name"]: c for c in profile["columns"]}
    units = cols["units"]
    assert units["min"] == 2
    assert units["max"] == 12
    assert units["mean"] is not None


def test_missing_values(agent):
    profile = agent.ingest(CSV_MISSING, "missing.csv")
    cols = {c["name"]: c for c in profile["columns"]}
    assert cols["score"]["null_count"] == 1
    assert cols["score"]["nullable"] is True


def test_schema_summary(agent):
    profile = agent.ingest(CSV_SALES, "sales.csv")
    summary = profile["schema_summary"]
    assert "sales.csv" in summary
    assert "units" in summary
    assert "revenue" in summary


def test_sample_rows(agent):
    profile = agent.ingest(CSV_SALES, "sales.csv")
    assert len(profile["sample_rows"]) == 5


def test_minimal_csv(agent):
    profile = agent.ingest(CSV_MINIMAL, "tiny.csv")
    assert profile["row_count"] == 2
    assert profile["col_count"] == 2


def test_invalid_csv(agent):
    with pytest.raises(ValueError):
        agent.ingest(b"\x00\xff\xfe", "bad.csv")
