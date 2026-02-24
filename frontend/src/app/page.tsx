"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import { Fish, RefreshCw, Waves } from "lucide-react";
import FileUpload from "@/components/FileUpload";
import DataSummary from "@/components/DataSummary";
import ChatMessage, { type Message } from "@/components/ChatMessage";
import SuggestedQuestions from "@/components/SuggestedQuestions";
import { queryData, type UploadResponse } from "@/lib/api";

export default function Home() {
  const [dataset, setDataset] = useState<UploadResponse | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef  = useRef<HTMLInputElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleUpload = useCallback((response: UploadResponse) => {
    setDataset(response);
    setMessages([
      {
        role: "assistant",
        response: {
          session_id: response.session_id,
          question: "",
          answer_summary: `I've analysed **${response.filename}** — ${response.row_count.toLocaleString()} rows and ${response.col_count} columns. Ask me anything about your data!`,
          pandas_code: "",
          result_type: "scalar",
          result_data: null,
          chart: { chart_type: "none", data: [], x_key: null, y_keys: [], title: "", show_chart: false },
          error: null,
        },
      },
    ]);
    setTimeout(() => inputRef.current?.focus(), 100);
  }, []);

  const handleReset = useCallback(() => {
    setDataset(null);
    setMessages([]);
    setInput("");
  }, []);

  const handleSubmit = useCallback(
    async (question: string) => {
      if (!dataset || !question.trim() || loading) return;
      const q = question.trim();
      setInput("");
      setMessages((prev) => [...prev, { role: "user", text: q }, { role: "thinking" }]);
      setLoading(true);

      try {
        const response = await queryData(dataset.session_id, q);
        setMessages((prev) => [
          ...prev.slice(0, -1), // remove thinking
          { role: "assistant", response },
        ]);
      } catch (e) {
        setMessages((prev) => [
          ...prev.slice(0, -1),
          {
            role: "error",
            text: e instanceof Error ? e.message : "Something went wrong.",
          },
        ]);
      } finally {
        setLoading(false);
        setTimeout(() => inputRef.current?.focus(), 100);
      }
    },
    [dataset, loading]
  );

  const onKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(input);
    }
  };

  return (
    <div className="min-h-screen flex flex-col">
      {/* ── Header ── */}
      <header className="sticky top-0 z-20 bg-white/80 backdrop-blur-md border-b border-slate-200 shadow-sm">
        <div className="max-w-5xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-ocean-400 to-ocean-600 flex items-center justify-center shadow-sm">
              <Fish className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="font-bold text-slate-800 leading-none">
                Gradient Fisherman
              </h1>
              <p className="text-xs text-slate-500 mt-0.5">
                SMB Data Assistant · DigitalOcean Gradient™ AI
              </p>
            </div>
          </div>
          {dataset && (
            <button
              onClick={handleReset}
              className="flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-700 transition-colors"
            >
              <RefreshCw className="w-4 h-4" />
              New dataset
            </button>
          )}
        </div>
      </header>

      {/* ── Main ── */}
      <main className="flex-1 max-w-5xl w-full mx-auto px-4 py-8 flex flex-col gap-6">
        {!dataset ? (
          /* ── Landing / Upload ── */
          <div className="flex flex-col items-center justify-center flex-1 gap-8 py-8">
            <div className="text-center max-w-xl">
              <div className="flex items-center justify-center gap-2 mb-4">
                <Waves className="w-8 h-8 text-ocean-400" />
              </div>
              <h2 className="text-3xl font-bold text-slate-800 mb-3">
                Ask your data anything
              </h2>
              <p className="text-slate-500 text-lg">
                Upload a CSV and ask questions in plain English.
                No SQL. No formulas. Instant charts.
              </p>
            </div>

            <FileUpload onUpload={handleUpload} />

            {/* Feature pills */}
            <div className="flex flex-wrap justify-center gap-2 text-sm text-slate-500">
              {[
                "📊 Auto-generates charts",
                "🔍 Natural language queries",
                "⚡ Powered by Claude Sonnet 4.6",
                "🔒 Data stays in your session",
              ].map((f) => (
                <span
                  key={f}
                  className="bg-white border border-slate-200 rounded-full px-3 py-1 shadow-sm"
                >
                  {f}
                </span>
              ))}
            </div>
          </div>
        ) : (
          /* ── Chat view ── */
          <div className="flex flex-col gap-4">
            <DataSummary data={dataset} />

            {/* Messages */}
            <div className="flex flex-col gap-4 min-h-[200px]">
              {messages.map((msg, i) => (
                <ChatMessage key={i} message={msg} />
              ))}
              <div ref={bottomRef} />
            </div>

            {/* Suggestions (only when no messages yet or last was assistant) */}
            {messages.length <= 1 && (
              <SuggestedQuestions
                columns={dataset.columns}
                onSelect={(q) => { setInput(q); handleSubmit(q); }}
              />
            )}

            {/* Input */}
            <div className="sticky bottom-4 bg-white border border-slate-200 rounded-2xl shadow-lg flex items-center gap-2 px-4 py-3">
              <input
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={onKeyDown}
                placeholder="Ask a question about your data…"
                disabled={loading}
                className="flex-1 text-sm outline-none text-slate-700 placeholder-slate-400 bg-transparent"
              />
              <button
                onClick={() => handleSubmit(input)}
                disabled={loading || !input.trim()}
                className="bg-ocean-500 hover:bg-ocean-600 disabled:opacity-40 disabled:cursor-not-allowed text-white text-sm font-medium px-4 py-2 rounded-xl transition-colors"
              >
                {loading ? (
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                ) : (
                  "Ask"
                )}
              </button>
            </div>
          </div>
        )}
      </main>

      {/* ── Footer ── */}
      <footer className="text-center text-xs text-slate-400 py-4 border-t border-slate-100">
        Built for the{" "}
        <a
          href="https://digitalocean.devpost.com"
          target="_blank"
          rel="noopener noreferrer"
          className="text-ocean-500 hover:underline"
        >
          DigitalOcean Gradient™ AI Hackathon
        </a>{" "}
        · Claude Sonnet 4.6 · Best Program for the People
      </footer>
    </div>
  );
}
