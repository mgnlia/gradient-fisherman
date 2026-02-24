"use client";

import { useCallback, useState } from "react";
import { Upload, FileText, AlertCircle, CheckCircle2 } from "lucide-react";
import { uploadCSV, type UploadResponse } from "@/lib/api";

interface Props {
  onUpload: (response: UploadResponse) => void;
}

export default function FileUpload({ onUpload }: Props) {
  const [dragging, setDragging] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFile = useCallback(
    async (file: File) => {
      if (!file.name.endsWith(".csv")) {
        setError("Please upload a CSV file.");
        return;
      }
      setError(null);
      setLoading(true);
      try {
        const response = await uploadCSV(file);
        onUpload(response);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Upload failed.");
      } finally {
        setLoading(false);
      }
    },
    [onUpload]
  );

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragging(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  const onInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  return (
    <div className="w-full max-w-2xl mx-auto">
      <label
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        className={[
          "flex flex-col items-center justify-center w-full h-52 border-2 border-dashed rounded-2xl cursor-pointer transition-all duration-200",
          dragging
            ? "border-ocean-500 bg-ocean-50 scale-[1.01]"
            : "border-ocean-300 bg-white hover:border-ocean-400 hover:bg-ocean-50",
          loading ? "pointer-events-none opacity-60" : "",
        ].join(" ")}
      >
        {loading ? (
          <div className="flex flex-col items-center gap-3 text-ocean-600">
            <div className="w-10 h-10 border-4 border-ocean-200 border-t-ocean-500 rounded-full animate-spin" />
            <span className="text-sm font-medium">Analysing your data…</span>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-3 text-ocean-500">
            <Upload className="w-10 h-10" />
            <div className="text-center">
              <p className="text-base font-semibold text-slate-700">
                Drop your CSV here
              </p>
              <p className="text-sm text-slate-500 mt-1">
                or <span className="text-ocean-600 underline">browse</span> to choose a file
              </p>
            </div>
            <p className="text-xs text-slate-400">CSV files up to 50 MB</p>
          </div>
        )}
        <input
          type="file"
          accept=".csv"
          className="hidden"
          onChange={onInputChange}
          disabled={loading}
        />
      </label>

      {error && (
        <div className="mt-3 flex items-center gap-2 text-red-600 text-sm">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          {error}
        </div>
      )}

      {/* Example datasets hint */}
      <p className="mt-4 text-xs text-center text-slate-400">
        Try it with your sales data, inventory sheet, or customer list
      </p>
    </div>
  );
}
