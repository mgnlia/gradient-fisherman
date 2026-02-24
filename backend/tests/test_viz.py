"""Tests for VizAgent."""

import pytest
from agents.viz_agent import VizAgent


@pytest.fixture
def agent():
    return VizAgent()


TABLE_DATA = [
    {"category": "Electronics", "revenue": 2100},
    {"category": "Clothing",    "revenue": 510},
    {"category": "Food",        "revenue": 800},
]

SCALAR_DATA = 42


def test_bar_chart(agent):
    cfg = agent.generate(
        result_data=TABLE_DATA,
        result_type="table",
        suggested_chart="bar",
        chart_x_col="category",
        chart_y_col="revenue",
        answer_summary="Revenue by category",
    )
    assert cfg["show_chart"] is True
    assert cfg["chart_type"] == "bar"
    assert cfg["x_key"] == "category"
    assert "revenue" in cfg["y_keys"]
    assert len(cfg["data"]) == 3


def test_scalar_no_chart(agent):
    cfg = agent.generate(
        result_data=SCALAR_DATA,
        result_type="scalar",
        suggested_chart="bar",
        chart_x_col=None,
        chart_y_col=None,
        answer_summary="Total",
    )
    assert cfg["show_chart"] is False


def test_empty_data_no_chart(agent):
    cfg = agent.generate(
        result_data=[],
        result_type="table",
        suggested_chart="bar",
        chart_x_col="x",
        chart_y_col="y",
        answer_summary="Nothing",
    )
    assert cfg["show_chart"] is False


def test_auto_chart_type(agent):
    """When suggested_chart is 'none', should still auto-pick bar."""
    cfg = agent.generate(
        result_data=TABLE_DATA,
        result_type="table",
        suggested_chart="none",
        chart_x_col="category",
        chart_y_col="revenue",
        answer_summary="Auto",
    )
    assert cfg["show_chart"] is True
    assert cfg["chart_type"] == "bar"


def test_pie_chart(agent):
    cfg = agent.generate(
        result_data=TABLE_DATA,
        result_type="table",
        suggested_chart="pie",
        chart_x_col="category",
        chart_y_col="revenue",
        answer_summary="Pie",
    )
    assert cfg["chart_type"] == "pie"
    assert cfg["show_chart"] is True
