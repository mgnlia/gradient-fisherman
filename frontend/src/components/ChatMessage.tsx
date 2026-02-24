"use client";

import { useState } from "react";
import { Bot, User, ChevronDown, ChevronUp, Code2 } from "lucide-react";
import ChartRenderer from "./ChartRenderer";
import ResultTable from "./ResultTable";
import type { QueryResponse } from "@/lib/api";

export type Message =
  | { role: "user"; text: string }
  | { role: "assistant"; response: QueryResponse }
  | { role: "error"; text: string }
  | { role: "thinking" };

interface Props {
  message: Message;
}

function CodeBlock({ code }: { code: string }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="mt-2">
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-600 transition-colors"
      >
        <Code2 className="w-3.5 h-3.5" />
        {open ? "Hide" : "Show"} generated code
        {open ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
      </button>
      {open && (
        <pre className="mt-1.5 p-3 bg-slate-900 text-green-400 rounded-lg text-xs overflow-x-auto">
          {code}
        </pre>
      )}
    </div>
  );
}

export default function ChatMessage({ message }: Props) {
  if (message.role === "thinking") {
    return (
      <div className="flex gap-3 message-enter">
        <div className="w-8 h-8 rounded-full bg-ocean-500 flex items-center justify-center flex-shrink-0">
          <Bot className="w-4 h-4 text-white" />
        </div>
        <div className="bg-white border border-slate-200 rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm">
          <div className="flex gap-1 items-center h-5">
            {[0, 1, 2].map((i) => (
              <div
                key={i}
                className="typing-dot w-2 h-2 bg-ocean-400 rounded-full"
                style={{ animationDelay: `${i * -0.16}s` }}
              />
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (message.role === "user") {
    return (
      <div className="flex gap-3 justify-end message-enter">
        <div className="bg-ocean-500 text-white rounded-2xl rounded-tr-sm px-4 py-3 max-w-[80%] shadow-sm">
          <p className="text-sm">{message.text}</p>
        </div>
        <div className="w-8 h-8 rounded-full bg-slate-200 flex items-center justify-center flex-shrink-0">
          <User className="w-4 h-4 text-slate-600" />
        </div>
      </div>
    );
  }

  if (message.role === "error") {
    return (
      <div className="flex gap-3 message-enter">
        <div className="w-8 h-8 rounded-full bg-red-100 flex items-center justify-center flex-shrink-0">
          <Bot className="w-4 h-4 text-red-500" />
        </div>
        <div className="bg-red-50 border border-red-200 rounded-2xl rounded-tl-sm px-4 py-3 text-sm text-red-700 shadow-sm">
          {message.text}
        </div>
      </div>
    );
  }

  // assistant
  const { response } = message;
  const hasTable =
    response.result_type === "table" &&
    Array.isArray(response.result_data) &&
    response.result_data.length > 0;

  return (
    <div className="flex gap-3 message-enter">
      <div className="w-8 h-8 rounded-full bg-ocean-500 flex items-center justify-center flex-shrink-0">
        <Bot className="w-4 h-4 text-white" />
      </div>
      <div className="flex-1 min-w-0 space-y-3">
        {/* Summary bubble */}
        <div className="bg-white border border-slate-200 rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm">
          <p className="text-sm text-slate-800">{response.answer_summary}</p>

          {/* Scalar result */}
          {response.result_type === "scalar" && response.result_data !== null && (
            <div className="mt-2 inline-block bg-ocean-50 border border-ocean-200 rounded-lg px-3 py-1.5">
              <span className="text-xl font-bold text-ocean-700">
                {typeof response.result_data === "number"
                  ? response.result_data.toLocaleString()
                  : String(response.result_data)}
              </span>
            </div>
          )}

          <CodeBlock code={response.pandas_code} />
        </div>

        {/* Chart */}
        {response.chart.show_chart && (
          <div className="bg-white border border-slate-200 rounded-2xl p-4 shadow-sm">
            <p className="text-xs font-medium text-slate-500 mb-3 uppercase tracking-wide">
              {response.chart.chart_type} chart
            </p>
            <ChartRenderer chart={response.chart} />
          </div>
        )}

        {/* Table */}
        {hasTable && (
          <div className="bg-white border border-slate-200 rounded-2xl overflow-hidden shadow-sm">
            <div className="px-4 py-2.5 border-b border-slate-100">
              <p className="text-xs font-medium text-slate-500 uppercase tracking-wide">
                Data table
              </p>
            </div>
            <div className="p-3">
              <ResultTable
                data={response.result_data as Record<string, unknown>[]}
              />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
