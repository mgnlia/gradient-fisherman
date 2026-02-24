'use client'

import { useState } from 'react'
import { ChevronDown, ChevronUp } from 'lucide-react'

interface DataTableProps {
  data: Record<string, unknown>[]
  maxRows?: number
}

export default function DataTable({ data, maxRows = 10 }: DataTableProps) {
  const [expanded, setExpanded] = useState(false)

  if (!data || data.length === 0) return null

  const columns = Object.keys(data[0])
  const displayData = expanded ? data : data.slice(0, maxRows)
  const hasMore = data.length > maxRows

  const formatCell = (value: unknown): string => {
    if (value === null || value === undefined || value === '') return '—'
    if (typeof value === 'number') {
      return value % 1 !== 0 ? value.toFixed(2) : value.toLocaleString()
    }
    return String(value)
  }

  return (
    <div className="mt-3 rounded-xl overflow-hidden" style={{ border: '1px solid rgba(0,128,255,0.2)' }}>
      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr style={{ background: 'rgba(0,128,255,0.15)' }}>
              {columns.map(col => (
                <th
                  key={col}
                  className="px-3 py-2 text-left font-semibold text-ocean-300 whitespace-nowrap"
                >
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {displayData.map((row, i) => (
              <tr
                key={i}
                className="border-t transition-colors hover:bg-white/5"
                style={{ borderColor: 'rgba(255,255,255,0.05)' }}
              >
                {columns.map(col => (
                  <td key={col} className="px-3 py-1.5 text-slate-300 whitespace-nowrap max-w-32 truncate">
                    {formatCell(row[col])}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {hasMore && (
        <button
          onClick={() => setExpanded(!expanded)}
          className="w-full flex items-center justify-center gap-1 py-2 text-xs text-slate-500 hover:text-ocean-300 transition-colors"
          style={{ borderTop: '1px solid rgba(255,255,255,0.05)' }}
        >
          {expanded ? (
            <><ChevronUp className="w-3.5 h-3.5" /> Show less</>
          ) : (
            <><ChevronDown className="w-3.5 h-3.5" /> Show all {data.length} rows</>
          )}
        </button>
      )}
    </div>
  )
}
