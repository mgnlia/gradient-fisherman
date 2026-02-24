"""
Tests for VizAgent — Recharts-compatible chart config generation.
Offline only: no network, no LLM.
"""
import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agents.viz_agent import VizAgent


@pytest.fixture
def viz():
    return VizAgent()


TABLE_DATA = [
    {"region": "North", "revenue": 1000},
    {"region": "South", "revenue": 2000},
    {"region": "East",  "revenue": 1500},
]


def test_bar_chart_generated(viz):
    cfg = viz.generate(
        result_data=TABLE_DATA,
        result_type="table",
        suggested_chart="bar",
        chart_x_col="region",
        chart_y_col="revenue",
        answer_summary="Revenue by region",
    )
    assert cfg["show_chart"] is True
    assert cfg["chart_type"] == "bar"
    assert cfg["x_key"] == "region"
    assert "revenue" in cfg["y_keys"]
    assert len(cfg["data"]) == 3


def test_scalar_result_no_chart(viz):
    cfg = viz.generate(
        result_data=42,
        result_type="scalar",
        suggested_chart="bar",
        chart_x_col=None,
        chart_y_col=None,
        answer_summary="Total revenue",
    )
    assert cfg["show_chart"] is False
    assert cfg["chart_type"] == "none"


def test_empty_data_no_chart(viz):
    cfg = viz.generate(
        result_data=[],
        result_type="table",
        suggested_chart="bar",
        chart_x_col="x",
        chart_y_col="y",
        answer_summary="Nothing",
    )
    assert cfg["show_chart"] is False


def test_unsupported_chart_type_falls_back(viz):
    """An unknown chart type should fall back to auto-detection (bar)."""
    cfg = viz.generate(
        result_data=TABLE_DATA,
        result_type="table",
        suggested_chart="radar",  # not in SUPPORTED
        chart_x_col="region",
        chart_y_col="revenue",
        answer_summary="Revenue by region",
    )
    assert cfg["show_chart"] is True
    assert cfg["chart_type"] in {"bar", "line", "pie", "scatter", "area"}


def test_none_chart_suggestion_auto_detects(viz):
    cfg = viz.generate(
        result_data=TABLE_DATA,
        result_type="table",
        suggested_chart="none",
        chart_x_col="region",
        chart_y_col="revenue",
        answer_summary="Revenue by region",
    )
    assert cfg["show_chart"] is True


def test_no_numeric_column_no_chart(viz):
    data = [{"a": "foo", "b": "bar"}, {"a": "baz", "b": "qux"}]
    cfg = viz.generate(
        result_data=data,
        result_type="table",
        suggested_chart="bar",
        chart_x_col="a",
        chart_y_col="b",
        answer_summary="Strings only",
    )
    assert cfg["show_chart"] is False


def test_nan_cleaned_from_output(viz):
    import math
    data = [{"cat": "A", "val": float("nan")}, {"cat": "B", "val": 10.0}]
    cfg = viz.generate(
        result_data=data,
        result_type="table",
        suggested_chart="bar",
        chart_x_col="cat",
        chart_y_col="val",
        answer_summary="NaN test",
    )
    # NaN row: val should be None in the output, not float nan
    val_a = next(r["val"] for r in cfg["data"] if r["cat"] == "A")
    assert val_a is None or (isinstance(val_a, float) and math.isnan(val_a)) is False
