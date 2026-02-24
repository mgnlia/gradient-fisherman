"""
Query Agent — translates natural language questions into pandas operations
using DigitalOcean Gradient™ AI inference, then executes them safely.
"""
import json
import traceback
import pandas as pd
import numpy as np
from typing import Any, Optional

from app.config import settings, get_gradient_client
from app.agents.ingest import get_dataset


SYSTEM_PROMPT = """You are a data analysis expert. You help small business owners analyze their CSV data.

Given a dataset schema and a user question, you MUST respond with a JSON object containing:
1. "pandas_code": A single Python expression using the variable `df` (a pandas DataFrame) that answers the question. 
   - Use only: filtering, groupby, agg, sort_values, head, value_counts, describe, sum, mean, max, min, count
   - Return a DataFrame or Series result
   - Do NOT use exec(), eval(), import, open(), or any file operations
   - Keep it to ONE expression
2. "answer_template": A template for the text answer. Use {result} as placeholder for the computed value.
3. "suggest_chart": One of "bar", "line", "pie", "scatter", "area", or null if no chart makes sense.
4. "chart_title": A short chart title, or null.

Example response:
{
  "pandas_code": "df.groupby('Category')['Revenue'].sum().sort_values(ascending=False).head(10)",
  "answer_template": "Here are the top categories by revenue: {result}",
  "suggest_chart": "bar",
  "chart_title": "Revenue by Category"
}

IMPORTANT: Respond ONLY with valid JSON. No markdown, no explanation outside the JSON."""


def _safe_eval_pandas(code: str, df: pd.DataFrame) -> Any:
    """
    Safely evaluate a pandas expression. Only allows DataFrame operations.
    Returns the result or raises an exception.
    """
    # Sanitize: block dangerous patterns
    blocked = ["import ", "exec(", "eval(", "open(", "__", "os.", "sys.", "subprocess"]
    for b in blocked:
        if b in code:
            raise ValueError(f"Blocked operation: {b}")
    
    # Execute in restricted namespace
    namespace = {
        "df": df.copy(),
        "pd": pd,
        "np": np,
    }
    result = eval(code, {"__builtins__": {}}, namespace)
    return result


def _result_to_table(result: Any) -> list[dict[str, Any]]:
    """Convert pandas result to JSON-serializable table."""
    if isinstance(result, pd.DataFrame):
        return result.head(50).fillna("").to_dict(orient="records")
    elif isinstance(result, pd.Series):
        return result.reset_index().head(50).fillna("").to_dict(orient="records")
    elif isinstance(result, (int, float, np.integer, np.floating)):
        return [{"value": float(result)}]
    else:
        return [{"value": str(result)}]


def _result_to_chart_data(result: Any, chart_type: str) -> tuple[list[dict], str, list[str]]:
    """Convert pandas result to Recharts-compatible data."""
    if isinstance(result, pd.Series):
        df_chart = result.reset_index()
        df_chart.columns = ["name", "value"]
        data = df_chart.head(20).fillna(0).to_dict(orient="records")
        return data, "name", ["value"]
    elif isinstance(result, pd.DataFrame):
        cols = result.columns.tolist()
        if len(cols) >= 2:
            # First col is x-axis, rest are y-axes
            data = result.head(20).fillna(0).to_dict(orient="records")
            return data, cols[0], cols[1:]
    return [], "name", ["value"]


def answer_question(
    question: str,
    dataset_id: str,
    conversation_history: list[dict],
) -> dict:
    """
    Main query agent function. Returns:
    {
        "answer": str,
        "table_data": list[dict] | None,
        "chart": ChartConfig dict | None,
        "raw_code": str | None,
    }
    """
    dataset = get_dataset(dataset_id)
    if not dataset:
        return {
            "answer": "I don't have any data loaded yet. Please upload a CSV file first! 📁",
            "table_data": None,
            "chart": None,
            "raw_code": None,
        }
    
    df = dataset["df"]
    schema_text = dataset["schema_text"]
    filename = dataset["filename"]
    
    # Build context for the AI
    schema_context = f"""Dataset: {filename}
Rows: {len(df)}
Columns and types:
{schema_text}

Column names exactly: {df.columns.tolist()}"""

    # Build conversation for multi-turn context
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    # Add limited history
    for msg in conversation_history[-6:]:  # last 3 turns
        if msg.get("role") in ("user", "assistant"):
            messages.append({"role": msg["role"], "content": msg["content"]})
    
    # Add current question with schema
    user_prompt = f"""Dataset schema:
{schema_context}

User question: {question}

Respond with JSON only."""
    
    messages.append({"role": "user", "content": user_prompt})
    
    try:
        client = get_gradient_client()
        response = client.chat.completions.create(
            model=settings.GRADIENT_MODEL,
            messages=messages,
            max_tokens=500,
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        
        raw_content = response.choices[0].message.content.strip()
        parsed = json.loads(raw_content)
        
        pandas_code = parsed.get("pandas_code", "")
        answer_template = parsed.get("answer_template", "Here are the results: {result}")
        suggest_chart = parsed.get("suggest_chart")
        chart_title = parsed.get("chart_title", question[:50])
        
    except Exception as e:
        return {
            "answer": f"I had trouble understanding that question. Could you rephrase it? (Error: {str(e)[:100]})",
            "table_data": None,
            "chart": None,
            "raw_code": None,
        }
    
    # Execute the pandas code
    try:
        result = _safe_eval_pandas(pandas_code, df)
        table_data = _result_to_table(result)
        
        # Format answer
        if isinstance(result, (int, float, np.integer, np.floating)):
            result_str = f"{float(result):,.2f}"
        elif isinstance(result, pd.Series) and len(result) <= 5:
            result_str = result.to_string()
        elif isinstance(result, pd.DataFrame) and len(result) <= 3:
            result_str = result.to_string(index=False)
        else:
            result_str = f"{len(table_data)} rows of data"
        
        answer = answer_template.replace("{result}", result_str)
        
        # Build chart config if applicable
        chart = None
        if suggest_chart and len(table_data) > 0:
            chart_data, x_key, y_keys = _result_to_chart_data(result, suggest_chart)
            if chart_data:
                chart = {
                    "chart_type": suggest_chart,
                    "title": chart_title or question[:60],
                    "data": chart_data,
                    "x_key": x_key,
                    "y_keys": y_keys,
                    "colors": ["#0080FF", "#00B4D8", "#48CAE4", "#90E0EF", "#ADE8F4"],
                }
        
        return {
            "answer": answer,
            "table_data": table_data if len(table_data) > 1 else None,
            "chart": chart,
            "raw_code": pandas_code,
        }
        
    except Exception as e:
        # Fallback: try to answer descriptively
        tb = traceback.format_exc()
        return {
            "answer": _fallback_answer(question, df, str(e)),
            "table_data": None,
            "chart": None,
            "raw_code": pandas_code,
        }


def _fallback_answer(question: str, df: pd.DataFrame, error: str) -> str:
    """Generate a helpful fallback answer when pandas execution fails."""
    try:
        client = get_gradient_client()
        # Provide basic stats for the model to use
        stats = df.describe(include="all").to_string()
        response = client.chat.completions.create(
            model=settings.GRADIENT_MODEL,
            messages=[{
                "role": "user",
                "content": f"""A user asked: "{question}"

Dataset statistics:
{stats[:1000]}

Answer the question using only the statistics above. Be concise (2-3 sentences)."""
            }],
            max_tokens=200,
            temperature=0.3,
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return (
            f"I couldn't compute an exact answer for that question. "
            f"Your dataset has {len(df)} rows and {len(df.columns)} columns. "
            f"Try rephrasing your question or asking something simpler!"
        )
