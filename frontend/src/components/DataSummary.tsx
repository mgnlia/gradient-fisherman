"use client";

import { FileText, Hash, Calendar, Tag, Type } from "lucide-react";
import type { UploadResponse, ColumnProfile } from "@/lib/api";

const DTYPE_ICONS: Record<string, React.ReactNode> = {
  numeric:     <Hash className="w-3.5 h-3.5" />,
  datetime:    <Calendar className="w-3.5 h-3.5" />,
  categorical: <Tag className="w-3.5 h-3.5" />,
  text:        <Type className="w-3.5 h-3.5" />,
};

const DTYPE_COLORS: Record<string, string> = {
  numeric:     "bg-blue-50 text-blue-700 border-blue-200",
  datetime:    "bg-purple-50 text-purple-700 border-purple-200",
  categorical: "bg-green-50 text-green-700 border-green-200",
  text:        "bg-slate-50 text-slate-600 border-slate-200",
};

function ColBadge({ col }: { col: ColumnProfile }) {
  const colors = DTYPE_COLORS[col.dtype] ?? DTYPE_COLORS.text;
  const icon   = DTYPE_ICONS[col.dtype];
  return (
    <div className={`flex items-center gap-1 px-2 py-1 rounded-full border text-xs font-medium ${colors}`}>
      {icon}
      <span className="max-w-[120px] truncate">{col.name}</span>
    </div>
  );
}

export default function DataSummary({ data }: { data: UploadResponse }) {
  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm">
      <div className="flex items-center gap-2 mb-4">
        <FileText className="w-5 h-5 text-ocean-500" />
        <h2 className="font-semibold text-slate-800">{data.filename}</h2>
      </div>

      <div className="flex gap-6 text-sm text-slate-600 mb-4">
        <span>
          <span className="font-semibold text-slate-800">
            {data.row_count.toLocaleString()}
          </span>{" "}
          rows
        </span>
        <span>
          <span className="font-semibold text-slate-800">{data.col_count}</span>{" "}
          columns
        </span>
      </div>

      <div className="flex flex-wrap gap-2">
        {data.columns.map((col) => (
          <ColBadge key={col.name} col={col} />
        ))}
      </div>
    </div>
  );
}
