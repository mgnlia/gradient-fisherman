"""Pydantic models for Gradient Fisherman API."""
from typing import Any, Optional
from pydantic import BaseModel


class ChatMessage(BaseModel):
    role: str  # "user" | "assistant" | "system"
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    session_id: str
    dataset_id: Optional[str] = None


class ChartConfig(BaseModel):
    chart_type: str  # "bar" | "line" | "pie" | "scatter" | "area"
    title: str
    data: list[dict[str, Any]]
    x_key: str
    y_keys: list[str]
    colors: Optional[list[str]] = None


class ChatResponse(BaseModel):
    message: str
    chart: Optional[ChartConfig] = None
    table_data: Optional[list[dict[str, Any]]] = None
    session_id: str


class UploadResponse(BaseModel):
    dataset_id: str
    filename: str
    rows: int
    columns: list[str]
    preview: list[dict[str, Any]]
    schema_summary: str


class DatasetInfo(BaseModel):
    dataset_id: str
    filename: str
    rows: int
    columns: list[str]
    dtypes: dict[str, str]
    sample_values: dict[str, list[Any]]
