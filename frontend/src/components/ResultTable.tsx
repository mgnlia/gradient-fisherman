"use client";

interface Props {
  data: Record<string, unknown>[];
  maxRows?: number;
}

export default function ResultTable({ data, maxRows = 20 }: Props) {
  if (!data || data.length === 0) return null;

  const cols = Object.keys(data[0]);
  const rows = data.slice(0, maxRows);
  const truncated = data.length > maxRows;

  return (
    <div className="overflow-x-auto rounded-xl border border-slate-200">
      <table className="min-w-full divide-y divide-slate-200 text-sm">
        <thead className="bg-slate-50">
          <tr>
            {cols.map((c) => (
              <th
                key={c}
                className="px-4 py-2.5 text-left font-semibold text-slate-600 whitespace-nowrap"
              >
                {c}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100 bg-white">
          {rows.map((row, i) => (
            <tr key={i} className="hover:bg-ocean-50 transition-colors">
              {cols.map((c) => (
                <td
                  key={c}
                  className="px-4 py-2 text-slate-700 whitespace-nowrap max-w-[200px] truncate"
                  title={String(row[c] ?? "")}
                >
                  {row[c] === null || row[c] === undefined
                    ? <span className="text-slate-300 italic">null</span>
                    : String(row[c])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      {truncated && (
        <p className="px-4 py-2 text-xs text-slate-400 bg-slate-50 border-t border-slate-200">
          Showing first {maxRows} of {data.length} rows
        </p>
      )}
    </div>
  );
}
