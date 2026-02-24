"use client";

import { Sparkles } from "lucide-react";

const GENERIC = [
  "What are the top 10 rows by the largest numeric column?",
  "Show me a summary of all numeric columns",
  "How many unique values does each column have?",
  "Which rows have missing values?",
  "Show me the distribution of the first categorical column",
];

interface Props {
  columns: Array<{ name: string; dtype: string }>;
  onSelect: (q: string) => void;
}

function generateSuggestions(
  columns: Array<{ name: string; dtype: string }>
): string[] {
  const numeric = columns.filter((c) => c.dtype === "numeric").map((c) => c.name);
  const cat     = columns.filter((c) => c.dtype === "categorical").map((c) => c.name);
  const dt      = columns.filter((c) => c.dtype === "datetime").map((c) => c.name);

  const suggestions: string[] = [];

  if (numeric.length >= 2) {
    suggestions.push(
      `What is the correlation between ${numeric[0]} and ${numeric[1]}?`
    );
  }
  if (numeric.length >= 1) {
    suggestions.push(`Show me the top 10 rows by ${numeric[0]}`);
    suggestions.push(`What is the total sum of ${numeric[0]}?`);
  }
  if (cat.length >= 1 && numeric.length >= 1) {
    suggestions.push(
      `Group by ${cat[0]} and sum ${numeric[0]}, show as a bar chart`
    );
  }
  if (dt.length >= 1 && numeric.length >= 1) {
    suggestions.push(
      `Show ${numeric[0]} over time using ${dt[0]} as a line chart`
    );
  }
  if (cat.length >= 1) {
    suggestions.push(`What are the most common values in ${cat[0]}?`);
  }

  // pad with generics if needed
  while (suggestions.length < 4) {
    suggestions.push(GENERIC[suggestions.length % GENERIC.length]);
  }

  return suggestions.slice(0, 4);
}

export default function SuggestedQuestions({ columns, onSelect }: Props) {
  const suggestions = generateSuggestions(columns);
  return (
    <div className="mb-4">
      <div className="flex items-center gap-1.5 text-xs font-medium text-slate-400 mb-2">
        <Sparkles className="w-3.5 h-3.5" />
        Try asking…
      </div>
      <div className="flex flex-wrap gap-2">
        {suggestions.map((q) => (
          <button
            key={q}
            onClick={() => onSelect(q)}
            className="text-xs bg-white border border-slate-200 text-slate-600 px-3 py-1.5 rounded-full hover:border-ocean-400 hover:text-ocean-600 hover:bg-ocean-50 transition-all"
          >
            {q}
          </button>
        ))}
      </div>
    </div>
  );
}
