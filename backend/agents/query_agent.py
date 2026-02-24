"""
Query Agent
===========
Translates a natural-language question into a pandas expression using
Claude Sonnet 4.6 on DigitalOcean Gradient™ AI, then executes it safely.
"""

from __future__ import annotations

import json
import re
import textwrap
from typing import Any

import numpy as np
import pandas as pd
from openai import AsyncOpenAI

# --------------------------------------------------------------------------- #
# System prompt                                                                #
# --------------------------------------------------------------------------- #

SYSTEM_PROMPT = textwrap.dedent("""
    You are a data analysis assistant for small business owners.
    You have access to a pandas DataFrame called `df`.

    Your task:
    1. Read the user's question and the dataset schema.
    2. Write ONE Python expression (no assignments, no imports) using pandas
       that answers the question. The expression must evaluate to a
       DataFrame, Series, scalar, or list.
    3. Return ONLY a JSON object — no markdown fences, no explanation.

    Required JSON format:
    {
      "pandas_code":    "<single pandas expression>",
      "result_type":    "table" | "scalar" | "series",
      "answer_summary": "<one-sentence plain-English answer>",
      "suggested_chart": "bar" | "line" | "pie" | "scatter" | "area" | "none",
      "chart_x_col":    "<column name for X axis, or null>",
      "chart_y_col":    "<column name for Y axis, or null>"
    }

    Rules:
    - pandas_code must be a SINGLE expression (no newlines, no semicolons).
    - NEVER use: exec, eval, open, import, os, sys, subprocess, __, globals, locals.
    - For aggregations use .reset_index() so the result is always a DataFrame.
    - If the question cannot be answered with available data, set
      pandas_code to "None" and explain in answer_summary.
    - Handle NaN gracefully (e.g. .fillna(0)).
    - For date filtering use pd.to_datetime() where needed.
""").strip()


# --------------------------------------------------------------------------- #
# Agent                                                                        #
# --------------------------------------------------------------------------- #

class QueryAgent:
    """NL → pandas via Gradient AI / Claude Sonnet 4.6, then safe execution."""

    _FORBIDDEN = [
        "__", "import ", "exec(", "eval(", "open(",
        "os.", "sys.", "subprocess", "globals(", "locals(",
    ]

    def __init__(self, client: AsyncOpenAI, model: str) -> None:
        self.client = client
        self.model = model

    # ---------------------------------------------------------------------- #
    # Public API                                                               #
    # ---------------------------------------------------------------------- #

    async def query(
        self,
        question: str,
        df: pd.DataFrame,
        schema_summary: str,
    ) -> dict[str, Any]:
        """
        Returns:
        {
            answer_summary, pandas_code, result_type,
            result_data, suggested_chart,
            chart_x_col, chart_y_col, error
        }
        """
        user_msg = f"Dataset schema:\n{schema_summary}\n\nQuestion: {question}"
        raw = await self._call_llm(user_msg)

        try:
            plan = self._parse(raw)
        except Exception as exc:
            return self._err(f"LLM parse error: {exc}", raw)

        code = plan.get("pandas_code") or "None"
        if code == "None":
            return {
                "answer_summary": plan.get("answer_summary", "Cannot answer this question."),
                "pandas_code": code,
                "result_type": "scalar",
                "result_data": None,
                "suggested_chart": "none",
                "chart_x_col": None,
                "chart_y_col": None,
                "error": None,
            }

        try:
            result_data, result_type = self._execute(code, df)
        except Exception as exc:
            return self._err(f"Execution error: {exc}", code)

        return {
            "answer_summary": plan.get("answer_summary", ""),
            "pandas_code": code,
            "result_type": result_type,
            "result_data": result_data,
            "suggested_chart": plan.get("suggested_chart", "none"),
            "chart_x_col": plan.get("chart_x_col"),
            "chart_y_col": plan.get("chart_y_col"),
            "error": None,
        }

    # ---------------------------------------------------------------------- #
    # Private helpers                                                          #
    # ---------------------------------------------------------------------- #

    async def _call_llm(self, user_msg: str) -> str:
        resp = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": user_msg},
            ],
            temperature=0.1,
            max_tokens=1024,
        )
        return resp.choices[0].message.content or ""

    def _parse(self, raw: str) -> dict:
        raw = raw.strip()
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        return json.loads(raw)

    def _execute(self, code: str, df: pd.DataFrame) -> tuple[Any, str]:
        for token in self._FORBIDDEN:
            if token in code:
                raise ValueError(f"Forbidden token '{token}' in generated code.")
        ns = {"df": df, "pd": pd, "np": np}
        result = eval(code, {"__builtins__": {}}, ns)  # noqa: S307
        return self._serialise(result)

    def _serialise(self, result: Any) -> tuple[Any, str]:
        if isinstance(result, pd.DataFrame):
            result = result.replace({np.nan: None})
            return result.to_dict(orient="records"), "table"
        if isinstance(result, pd.Series):
            df_out = result.replace({np.nan: None}).reset_index()
            df_out.columns = [str(c) for c in df_out.columns]
            return df_out.to_dict(orient="records"), "table"
        if isinstance(result, np.integer):
            return int(result), "scalar"
        if isinstance(result, np.floating):
            return round(float(result), 4), "scalar"
        if isinstance(result, np.bool_):
            return bool(result), "scalar"
        if isinstance(result, (list, tuple)):
            return list(result), "list"
        return result, "scalar"

    def _err(self, msg: str, ctx: str = "") -> dict[str, Any]:
        return {
            "answer_summary": f"Sorry, I couldn't answer that. {msg}",
            "pandas_code": ctx,
            "result_type": "scalar",
            "result_data": None,
            "suggested_chart": "none",
            "chart_x_col": None,
            "chart_y_col": None,
            "error": msg,
        }
