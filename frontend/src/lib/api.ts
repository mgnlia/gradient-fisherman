const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface ColumnProfile {
  name: string;
  dtype: "numeric" | "categorical" | "datetime" | "text";
  pandas_dtype: string;
  nullable: boolean;
  null_count: number;
  unique_count: number;
  sample_values: unknown[];
  min: unknown;
  max: unknown;
  mean: number | null;
  top_values: string[] | null;
}

export interface UploadResponse {
  session_id: string;
  filename: string;
  row_count: number;
  col_count: number;
  columns: ColumnProfile[];
  sample_rows: Record<string, unknown>[];
  schema_summary: string;
}

export interface ChartConfig {
  chart_type: "bar" | "line" | "pie" | "scatter" | "area" | "none";
  data: Record<string, unknown>[];
  x_key: string | null;
  y_keys: string[];
  title: string;
  show_chart: boolean;
}

export interface QueryResponse {
  session_id: string;
  question: string;
  answer_summary: string;
  pandas_code: string;
  result_type: "table" | "scalar" | "series" | "list";
  result_data: unknown;
  chart: ChartConfig;
  error: string | null;
}

export async function uploadCSV(file: File): Promise<UploadResponse> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API_URL}/upload`, { method: "POST", body: form });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Upload failed (${res.status})`);
  }
  return res.json();
}

export async function queryData(
  sessionId: string,
  question: string
): Promise<QueryResponse> {
  const res = await fetch(`${API_URL}/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, question }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Query failed (${res.status})`);
  }
  return res.json();
}

export async function checkHealth(): Promise<boolean> {
  try {
    const res = await fetch(`${API_URL}/health`, { cache: "no-store" });
    return res.ok;
  } catch {
    return false;
  }
}
