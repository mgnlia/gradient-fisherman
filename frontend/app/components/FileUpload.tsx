'use client'

import { useState, useRef, useCallback } from 'react'
import { Upload, FileText, CheckCircle, AlertCircle, X } from 'lucide-react'

interface UploadResult {
  dataset_id: string
  filename: string
  rows: number
  columns: string[]
  preview: Record<string, unknown>[]
  schema_summary: string
}

interface FileUploadProps {
  onUploadSuccess: (result: UploadResult) => void
  currentDataset: UploadResult | null
  onClearDataset: () => void
}

export default function FileUpload({ onUploadSuccess, currentDataset, onClearDataset }: FileUploadProps) {
  const [isDragging, setIsDragging] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleUpload = useCallback(async (file: File) => {
    if (!file.name.endsWith('.csv')) {
      setError('Please upload a CSV file.')
      return
    }
    if (file.size > 10 * 1024 * 1024) {
      setError('File too large. Maximum size is 10MB.')
      return
    }

    setIsUploading(true)
    setError(null)

    const formData = new FormData()
    formData.append('file', file)

    try {
      const res = await fetch('/api/upload', {
        method: 'POST',
        body: formData,
      })

      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || 'Upload failed')
      }

      const result: UploadResult = await res.json()
      onUploadSuccess(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed. Please try again.')
    } finally {
      setIsUploading(false)
    }
  }, [onUploadSuccess])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    const file = e.dataTransfer.files[0]
    if (file) handleUpload(file)
  }, [handleUpload])

  const handleFileChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) handleUpload(file)
  }, [handleUpload])

  const loadDemoData = useCallback(async () => {
    setIsUploading(true)
    setError(null)
    try {
      // Fetch the demo CSV from public folder
      const csvRes = await fetch('/shopify_demo.csv')
      const csvText = await csvRes.text()
      const blob = new Blob([csvText], { type: 'text/csv' })
      const file = new File([blob], 'shopify_demo.csv', { type: 'text/csv' })
      await handleUpload(file)
    } catch {
      setError('Failed to load demo data.')
    } finally {
      setIsUploading(false)
    }
  }, [handleUpload])

  if (currentDataset) {
    return (
      <div className="glass-card rounded-xl p-4">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg flex items-center justify-center" style={{ background: 'rgba(0,128,255,0.2)' }}>
              <CheckCircle className="w-5 h-5 text-ocean-400" />
            </div>
            <div>
              <p className="text-sm font-semibold text-white">{currentDataset.filename}</p>
              <p className="text-xs text-slate-400">
                {currentDataset.rows.toLocaleString()} rows · {currentDataset.columns.length} columns
              </p>
            </div>
          </div>
          <button
            onClick={onClearDataset}
            className="text-slate-500 hover:text-slate-300 transition-colors p-1"
            title="Remove dataset"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
        <p className="mt-3 text-xs text-slate-400 leading-relaxed">{currentDataset.schema_summary}</p>
        <div className="mt-2 flex flex-wrap gap-1">
          {currentDataset.columns.slice(0, 6).map(col => (
            <span key={col} className="text-xs px-2 py-0.5 rounded-full" style={{ background: 'rgba(0,128,255,0.15)', color: '#90E0EF' }}>
              {col}
            </span>
          ))}
          {currentDataset.columns.length > 6 && (
            <span className="text-xs px-2 py-0.5 rounded-full text-slate-500" style={{ background: 'rgba(255,255,255,0.05)' }}>
              +{currentDataset.columns.length - 6} more
            </span>
          )}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      <div
        className={`relative rounded-xl border-2 border-dashed transition-all cursor-pointer ${
          isDragging
            ? 'border-ocean-500 bg-ocean-900/30'
            : 'border-slate-600 hover:border-ocean-600 hover:bg-white/5'
        }`}
        onDragOver={(e) => { e.preventDefault(); setIsDragging(true) }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv"
          className="hidden"
          onChange={handleFileChange}
        />
        <div className="p-6 text-center">
          {isUploading ? (
            <div className="flex flex-col items-center gap-3">
              <div className="w-10 h-10 rounded-full border-2 border-ocean-500 border-t-transparent animate-spin" />
              <p className="text-sm text-slate-400">Analyzing your data...</p>
            </div>
          ) : (
            <div className="flex flex-col items-center gap-3">
              <div className="w-12 h-12 rounded-xl flex items-center justify-center" style={{ background: 'rgba(0,128,255,0.15)' }}>
                <Upload className="w-6 h-6 text-ocean-400" />
              </div>
              <div>
                <p className="text-sm font-medium text-white">Drop CSV file here</p>
                <p className="text-xs text-slate-500 mt-1">or click to browse · max 10MB</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {error && (
        <div className="flex items-center gap-2 text-red-400 text-xs px-3 py-2 rounded-lg" style={{ background: 'rgba(239,68,68,0.1)' }}>
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      <button
        onClick={loadDemoData}
        disabled={isUploading}
        className="w-full flex items-center justify-center gap-2 text-xs text-slate-400 hover:text-ocean-300 transition-colors py-2 rounded-lg hover:bg-white/5 disabled:opacity-50"
      >
        <FileText className="w-3.5 h-3.5" />
        Try with Shopify demo data
      </button>
    </div>
  )
}
