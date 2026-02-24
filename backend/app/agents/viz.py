"""
Viz Agent — generates chart recommendations and configurations
using DigitalOcean Gradient™ AI inference.
"""
import json
from typing import Any, Optional

from app.config import settings, get_gradient_client


def recommend_chart(
    question: str,
    data: list[dict[str, Any]],
    current_chart_type: Optional[str] = None,
) -> dict:
    """
    Ask Gradient™ AI to recommend the best chart type for the data.
    Returns updated chart config.
    """
    if not data:
        return {}
    
    # Infer keys from data
    if not data:
        return {}
    
    keys = list(data[0].keys())
    sample = data[:3]
    
    try:
        client = get_gradient_client()
        prompt = f"""Given this data and question, recommend the best chart type.

Question: {question}
Data keys: {keys}
Sample rows: {json.dumps(sample, default=str)}
Current chart type: {current_chart_type or 'none'}

Respond with JSON:
{{
  "chart_type": "bar|line|pie|scatter|area",
  "x_key": "<key for x-axis>",
  "y_keys": ["<key1>", "<key2>"],
  "reasoning": "<one sentence>"
}}"""

        response = client.chat.completions.create(
            model=settings.GRADIENT_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        
        result = json.loads(response.choices[0].message.content)
        return result
    except Exception:
        # Heuristic fallback
        numeric_keys = [k for k in keys if k not in ("name", "index", "label", "category")]
        label_keys = [k for k in keys if k in ("name", "index", "label", "category")]
        
        return {
            "chart_type": current_chart_type or "bar",
            "x_key": label_keys[0] if label_keys else keys[0],
            "y_keys": numeric_keys[:2] if numeric_keys else keys[1:2],
            "reasoning": "Heuristic recommendation",
        }


def generate_insight(
    question: str,
    data: list[dict[str, Any]],
    chart_type: str,
) -> str:
    """
    Generate a one-sentence insight about the chart data.
    """
    if not data:
        return ""
    
    try:
        client = get_gradient_client()
        prompt = f"""Given this {chart_type} chart data answering "{question}", write ONE sentence insight about the most interesting pattern or finding. Be specific with numbers if available.

Data (first 5 rows): {json.dumps(data[:5], default=str)}

Respond with just the insight sentence, no preamble."""

        response = client.chat.completions.create(
            model=settings.GRADIENT_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100,
            temperature=0.4,
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return ""
