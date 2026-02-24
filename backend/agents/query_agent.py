"""
Query Agent
===========
Translates a natural-language question into a pandas expression using
Claude Sonnet 4.6 on DigitalOcean Gradient™ AI, then executes it safely.

Security: AST-level validation before eval() — whitelists every node type,
blocks __class__/__bases__ attribute chains, import statements, and all
non-whitelisted builtins. String-matching denylists are NOT used because
they are trivially bypassable via Python's class hierarchy.
"""

from __future__ import annotations

import ast
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
# AST-level security validator                                                 #
# --------------------------------------------------------------------------- #

# Whitelisted AST node types.  Every node in the generated expression must
# be one of these; anything else (Import, FunctionDef, ClassDef, …) raises.
_ALLOWED_NODE_TYPES = frozenset({
    # Literals & collections
    ast.Constant,
    ast.List, ast.Tuple, ast.Set, ast.Dict,
    # Name / attribute access (validated separately)
    ast.Name, ast.Attribute,
    # Operators
    ast.BinOp, ast.UnaryOp, ast.BoolOp, ast.Compare,
    ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow,
    ast.USub, ast.UAdd, ast.Not,
    ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE,
    ast.And, ast.Or, ast.In, ast.NotIn,
    # Subscript / slice
    ast.Subscript, ast.Index, ast.Slice,
    # Call & keyword
    ast.Call, ast.keyword,
    # Expression wrappers
    ast.Expr, ast.Expression,
    # Comprehensions
    ast.ListComp, ast.SetComp, ast.DictComp,
    ast.comprehension, ast.IfExp,
    # Starred
    ast.Starred,
    # Contexts
    ast.Load, ast.Store, ast.Del,
})

# Top-level names allowed in the eval namespace
_ALLOWED_NAMES = frozenset({
    "df", "pd", "np",
    "True", "False", "None",
    "len", "range", "list", "dict", "set", "tuple",
    "str", "int", "float", "bool",
    "round", "abs", "min", "max", "sum", "sorted",
    "enumerate", "zip", "print",
})

# Attribute names that are unconditionally forbidden regardless of object.
# This blocks __class__.__bases__[0].__subclasses__() and similar chains.
_FORBIDDEN_ATTRS = frozenset({
    "__class__", "__bases__", "__subclasses__", "__mro__",
    "__globals__", "__locals__", "__builtins__", "__import__",
    "__reduce__", "__reduce_ex__", "__getattribute__",
    "__init__", "__new__", "__del__",
    "system", "popen", "subprocess", "exec", "eval",
    "compile", "open", "read", "write", "unlink", "remove",
    "globals", "locals", "vars", "dir",
})


class _ASTValidator(ast.NodeVisitor):
    """Walk the AST and raise ValueError on any disallowed construct."""

    def generic_visit(self, node: ast.AST) -> None:
        if type(node) not in _ALLOWED_NODE_TYPES:
            raise ValueError(
                f"Disallowed AST node: {type(node).__name__}. "
                "Only pure pandas/numpy expressions are permitted."
            )
        super().generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        if node.id not in _ALLOWED_NAMES:
            raise ValueError(
                f"Disallowed name '{node.id}'. "
                "Only 'df', 'pd', 'np', and standard builtins are allowed."
            )
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        if node.attr in _FORBIDDEN_ATTRS:
            raise ValueError(
                f"Forbidden attribute '.{node.attr}' — not permitted in data queries."
            )
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        if isinstance(node.func, ast.Name) and node.func.id not in _ALLOWED_NAMES:
            raise ValueError(
                f"Disallowed call '{node.func.id}()'. "
                "Only whitelisted functions are permitted."
            )
        self.generic_visit(node)


def _validate_ast(code: str) -> None:
    """
    Parse `code` as a Python expression and walk the AST.
    Raises ValueError with a descriptive message on any violation.
    """
    try:
        tree = ast.parse(code, mode="eval")
    except SyntaxError as exc:
        raise ValueError(f"Invalid Python expression: {exc}") from exc
    _ASTValidator().visit(tree)


# --------------------------------------------------------------------------- #
# Agent                                                                        #
# --------------------------------------------------------------------------- #

class QueryAgent:
    """NL → pandas via Gradient AI / Claude Sonnet 4.6, then safe AST-validated execution."""

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
        """
        Safely evaluate a pandas expression.

        Defence-in-depth:
        1. AST parse + whitelist walk — blocks attribute traversal attacks,
           __class__.__bases__ chains, import statements, etc.
        2. Restricted builtins namespace (belt-and-suspenders).
        3. Fresh df copy so mutations don't affect the stored dataset.
        """
        # Step 1: AST validation — raises ValueError on any violation
        _validate_ast(code)

        # Step 2: Minimal explicit namespace
        safe_builtins = {
            "len": len, "range": range, "list": list, "dict": dict,
            "set": set, "tuple": tuple, "str": str, "int": int,
            "float": float, "bool": bool, "round": round, "abs": abs,
            "min": min, "max": max, "sum": sum, "sorted": sorted,
            "enumerate": enumerate, "zip": zip, "print": print,
            "True": True, "False": False, "None": None,
        }
        ns = {
            "__builtins__": safe_builtins,
            "df": df.copy(),
            "pd": pd,
            "np": np,
        }

        # Step 3: Execute — AST validation already blocked dangerous paths
        result = eval(code, ns)  # noqa: S307 — guarded by AST validation above
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
