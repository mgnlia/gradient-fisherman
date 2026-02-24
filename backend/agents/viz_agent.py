"""
Viz Agent
=========
Converts query results into a Recharts-compatible chart configuration.
No LLM call — chart type comes from the Query Agent's suggestion.
"""

from __future__ import annotations

from typing import Any

import numpy as np


SUPPORTED = {"bar", "line", "pie", "scatter", "area"}


class VizAgent:

    def generate(
        self,
        result_data: list[dict] | Any,
        result_type: str,
        suggested_chart: str,
        chart_x_col: str | None,
        chart_y_col: str | None,
        answer_summary: str,
    ) -> dict[str, Any]:
        """
        Returns a chart config:
        {
            chart_type, data, x_key, y_keys, title, show_chart
        }
        """
        if result_type == "scalar" or not isinstance(result_data, list) or not result_data:
            return self._none(answer_summary)

        chart_type = suggested_chart if suggested_chart in SUPPORTED else "none"
        if chart_type == "none":
            chart_type = self._auto(result_data)
        if chart_type == "none":
            return self._none(answer_summary)

        cols = list(result_data[0].keys())
        x_key = chart_x_col if chart_x_col in cols else cols[0]
        numeric = [c for c in cols if c != x_key and self._is_numeric(result_data, c)]

        if chart_y_col and chart_y_col in numeric:
            y_keys = [chart_y_col]
        elif numeric:
            y_keys = numeric[:3]
        else:
            return self._none(answer_summary)

        return {
            "chart_type": chart_type,
            "data": self._clean(result_data, x_key, y_keys),
            "x_key": x_key,
            "y_keys": y_keys,
            "title": answer_summary,
            "show_chart": True,
        }

    # ---------------------------------------------------------------------- #

    def _auto(self, data: list[dict]) -> str:
        cols = list(data[0].keys())
        if len(cols) < 2:
            return "none"
        numeric = [c for c in cols if self._is_numeric(data, c)]
        return "bar" if numeric else "none"

    def _is_numeric(self, data: list[dict], col: str) -> bool:
        vals = [r.get(col) for r in data[:10] if r.get(col) is not None]
        return bool(vals) and all(isinstance(v, (int, float)) for v in vals)

    def _clean(
        self, data: list[dict], x_key: str | None, y_keys: list[str]
    ) -> list[dict]:
        keep = {k for k in [x_key] + y_keys if k}
        cleaned = []
        for row in data:
            entry: dict[str, Any] = {}
            for k, v in row.items():
                if k not in keep:
                    continue
                if isinstance(v, float) and v != v:  # NaN
                    entry[k] = None
                elif hasattr(v, "item"):              # numpy scalar
                    entry[k] = v.item()
                else:
                    entry[k] = v
            cleaned.append(entry)
        return cleaned

    def _none(self, title: str) -> dict[str, Any]:
        return {
            "chart_type": "none",
            "data": [],
            "x_key": None,
            "y_keys": [],
            "title": title,
            "show_chart": False,
        }
