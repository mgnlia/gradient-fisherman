"""
Ingest Agent
============
Parses an uploaded CSV, infers column types, and builds a rich data profile
that the Query Agent uses as LLM context.  No LLM call needed here — pure
pandas analysis.
"""

from __future__ import annotations

import io
from typing import Any

import numpy as np
import pandas as pd


class IngestAgent:
    MAX_ROWS = 100_000
    SAMPLE_ROWS = 5
    CATEGORICAL_THRESHOLD = 0.05   # unique_count / total < 5 % → categorical
    CATEGORICAL_ABS_MAX = 50       # or fewer than 50 distinct values

    # ---------------------------------------------------------------------- #
    # Public API                                                               #
    # ---------------------------------------------------------------------- #

    def ingest(self, file_bytes: bytes, filename: str) -> dict[str, Any]:
        """
        Parse CSV bytes and return a DataProfile dict.

        Schema:
        {
            filename, row_count, col_count,
            columns: [{
                name, dtype, pandas_dtype, nullable, null_count,
                unique_count, sample_values,
                min, max, mean,          # numeric / datetime
                top_values,              # categorical
            }],
            sample_rows: [dict, ...],
            schema_summary: str,         # human-readable block for LLM prompt
        }
        """
        try:
            df = pd.read_csv(io.BytesIO(file_bytes), nrows=self.MAX_ROWS)
        except Exception as exc:
            raise ValueError(f"Cannot parse '{filename}': {exc}") from exc

        df = self._coerce_datetimes(df)
        columns = [self._profile_col(df, c) for c in df.columns]
        sample_rows = (
            df.head(self.SAMPLE_ROWS)
            .replace({np.nan: None})
            .to_dict(orient="records")
        )

        return {
            "filename": filename,
            "row_count": len(df),
            "col_count": len(df.columns),
            "columns": columns,
            "sample_rows": sample_rows,
            "schema_summary": self._schema_summary(filename, df, columns),
        }

    # ---------------------------------------------------------------------- #
    # Private helpers                                                          #
    # ---------------------------------------------------------------------- #

    def _coerce_datetimes(self, df: pd.DataFrame) -> pd.DataFrame:
        for col in df.select_dtypes(include="object").columns:
            sample = df[col].dropna().head(20)
            if sample.empty:
                continue
            try:
                parsed = pd.to_datetime(sample, infer_datetime_format=True)
                if parsed.notna().all():
                    df[col] = pd.to_datetime(
                        df[col], infer_datetime_format=True, errors="coerce"
                    )
            except Exception:
                pass
        return df

    def _profile_col(self, df: pd.DataFrame, col: str) -> dict[str, Any]:
        s = df[col]
        null_count = int(s.isna().sum())
        unique_count = int(s.nunique(dropna=True))
        sample_values = [_py(v) for v in s.dropna().head(5).tolist()]
        n = len(df)

        base: dict[str, Any] = {
            "name": col,
            "pandas_dtype": str(s.dtype),
            "nullable": null_count > 0,
            "null_count": null_count,
            "unique_count": unique_count,
            "sample_values": sample_values,
            "min": None,
            "max": None,
            "mean": None,
            "top_values": None,
        }

        if pd.api.types.is_numeric_dtype(s):
            base["dtype"] = "numeric"
            non_null = s.dropna()
            if not non_null.empty:
                base["min"] = _py(non_null.min())
                base["max"] = _py(non_null.max())
                base["mean"] = round(float(non_null.mean()), 4)

        elif pd.api.types.is_datetime64_any_dtype(s):
            base["dtype"] = "datetime"
            non_null = s.dropna()
            if not non_null.empty:
                base["min"] = str(non_null.min())
                base["max"] = str(non_null.max())

        elif unique_count <= self.CATEGORICAL_ABS_MAX or (
            n > 0 and unique_count / n < self.CATEGORICAL_THRESHOLD
        ):
            base["dtype"] = "categorical"
            top = s.value_counts().head(10).index.tolist()
            base["top_values"] = [str(v) for v in top]

        else:
            base["dtype"] = "text"

        return base

    def _schema_summary(
        self, filename: str, df: pd.DataFrame, columns: list[dict]
    ) -> str:
        lines = [
            f"Dataset: {filename}",
            f"Rows: {len(df):,}  |  Columns: {len(df.columns)}",
            "",
            "Columns:",
        ]
        for c in columns:
            dtype = c["dtype"]
            extras = ""
            if dtype == "numeric":
                extras = f" [min={c['min']}, max={c['max']}, mean={c['mean']}]"
            elif dtype == "datetime":
                extras = f" [from {c['min']} to {c['max']}]"
            elif dtype == "categorical" and c["top_values"]:
                top = ", ".join(c["top_values"][:5])
                extras = f" [values: {top}]"
            nulls = f" ({c['null_count']} nulls)" if c["null_count"] else ""
            lines.append(f"  • {c['name']} ({dtype}){nulls}{extras}")
        return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Utility                                                                      #
# --------------------------------------------------------------------------- #

def _py(val: Any) -> Any:
    """Convert numpy scalar → native Python for JSON serialisation."""
    if isinstance(val, np.integer):
        return int(val)
    if isinstance(val, np.floating):
        return float(val)
    if isinstance(val, np.bool_):
        return bool(val)
    return val
