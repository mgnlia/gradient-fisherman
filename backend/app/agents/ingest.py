"""
Ingest Agent — parses CSV files, detects schema, stores in-memory dataset registry.
Uses DigitalOcean Gradient™ AI inference to generate human-readable schema summaries.
"""
import io
import uuid
import pandas as pd
from typing import Any
from openai import OpenAI

from app.config import settings, get_gradient_client

# In-memory dataset store: { dataset_id: { "df": pd.DataFrame, "meta": DatasetMeta } }
_dataset_store: dict[str, dict] = {}


def _infer_column_description(col: str, dtype: str, sample_values: list) -> str:
    """Quick heuristic description for a column."""
    col_lower = col.lower()
    if any(k in col_lower for k in ["date", "time", "created", "updated"]):
        return "datetime"
    if any(k in col_lower for k in ["price", "revenue", "cost", "amount", "total", "sale"]):
        return "currency"
    if any(k in col_lower for k in ["id", "sku", "code", "ref"]):
        return "identifier"
    if any(k in col_lower for k in ["qty", "quantity", "count", "num", "stock"]):
        return "quantity"
    if any(k in col_lower for k in ["name", "title", "product", "item", "category"]):
        return "label"
    return dtype


def parse_csv(content: bytes, filename: str) -> dict:
    """
    Parse CSV bytes into a DataFrame and register it.
    Returns dataset metadata dict.
    """
    df = pd.read_csv(io.BytesIO(content))
    
    # Coerce date columns
    for col in df.columns:
        if any(k in col.lower() for k in ["date", "time", "created", "updated"]):
            try:
                df[col] = pd.to_datetime(df[col], errors="coerce")
            except Exception:
                pass

    dataset_id = str(uuid.uuid4())
    
    # Build schema summary
    schema_info = []
    sample_values = {}
    for col in df.columns:
        dtype_str = str(df[col].dtype)
        samples = df[col].dropna().head(3).tolist()
        sample_values[col] = [str(s) for s in samples]
        desc = _infer_column_description(col, dtype_str, samples)
        schema_info.append(f"- {col} ({desc}): {', '.join(str(s) for s in samples[:2])}")

    schema_text = "\n".join(schema_info)
    
    # Generate AI schema summary via Gradient™ AI
    schema_summary = _generate_schema_summary(filename, df, schema_text)
    
    _dataset_store[dataset_id] = {
        "df": df,
        "filename": filename,
        "schema_summary": schema_summary,
        "schema_text": schema_text,
        "sample_values": sample_values,
    }
    
    return {
        "dataset_id": dataset_id,
        "filename": filename,
        "rows": len(df),
        "columns": df.columns.tolist(),
        "preview": df.head(5).fillna("").to_dict(orient="records"),
        "schema_summary": schema_summary,
    }


def _generate_schema_summary(filename: str, df: pd.DataFrame, schema_text: str) -> str:
    """Use Gradient™ AI to generate a friendly schema description."""
    try:
        client = get_gradient_client()
        prompt = f"""You are a data analyst assistant. A user uploaded a CSV file named "{filename}" with {len(df)} rows and {len(df.columns)} columns.

Here are the columns and sample values:
{schema_text}

Write a 2-3 sentence friendly summary of what this dataset contains and what kinds of questions a business owner could ask about it. Be concise and practical."""

        response = client.chat.completions.create(
            model=settings.GRADIENT_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.3,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        # Fallback summary if API unavailable
        return (
            f"Dataset '{filename}' with {len(df)} rows and {len(df.columns)} columns: "
            f"{', '.join(df.columns.tolist()[:5])}{'...' if len(df.columns) > 5 else ''}. "
            "Ask questions about this data in plain English."
        )


def get_dataset(dataset_id: str) -> dict | None:
    """Retrieve a registered dataset by ID."""
    return _dataset_store.get(dataset_id)


def list_datasets() -> list[str]:
    """List all registered dataset IDs."""
    return list(_dataset_store.keys())
