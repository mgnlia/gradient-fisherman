'use client'

import { useState, useEffect } from 'react'
import { v4 as uuidv4 } from 'uuid'
import { Github, ExternalLink, Fish, Waves } from 'lucide-react'
import FileUpload from './components/FileUpload'
import ChatWindow from './components/ChatWindow'

interface UploadResult {
  dataset_id: string
  filename: string
  rows: number
  columns: string[]
  preview: Record<string, unknown>[]
  schema_summary: string
}

export default function Home() {
  const [dataset, setDataset] = useState<UploadResult | null>(null)
  const [sessionId] = useState(() => uuidv4())
  const [sidebarOpen, setSidebarOpen] = useState(true)

  return (
    <div className="min-h-screen ocean-bg flex flex-col">
      {/* Header */}
      <header className="glass-card border-b border-white/10 px-6 py-4 flex items-center justify-between flex-shrink-0">
        <div className="flex items-center gap-3">
          <div className="fish-float text-3xl">🎣</div>
          <div>
            <h1 className="text-xl font-bold text-white">Gradient Fisherman</h1>
            <p className="text-xs text-slate-400">AI Data Assistant for Small Businesses</p>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <div className="hidden md:flex items-center gap-2 text-xs text-slate-500">
            <span>Powered by</span>
            <span className="font-semibold text-do-blue">DigitalOcean Gradient™ AI</span>
          </div>
          <a
            href="https://github.com/mgnlia/gradient-fisherman"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 text-xs text-slate-400 hover:text-white transition-colors px-3 py-1.5 rounded-lg hover:bg-white/10"
          >
            <Github className="w-4 h-4" />
            <span className="hidden sm:inline">GitHub</span>
          </a>
        </div>
      </header>

      {/* Main content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <aside
          className={`flex-shrink-0 transition-all duration-300 ${
            sidebarOpen ? 'w-80' : 'w-0'
          } overflow-hidden`}
          style={{ borderRight: '1px solid rgba(255,255,255,0.08)' }}
        >
          <div className="w-80 h-full flex flex-col p-5 space-y-6 overflow-y-auto">
            {/* Upload section */}
            <div>
              <h2 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                <span>📁</span> Your Data
              </h2>
              <FileUpload
                onUploadSuccess={setDataset}
                currentDataset={dataset}
                onClearDataset={() => setDataset(null)}
              />
            </div>

            {/* How it works */}
            <div>
              <h2 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                <span>🌊</span> How It Works
              </h2>
              <div className="space-y-3">
                {[
                  { icon: '📤', title: 'Upload CSV', desc: 'Drop any CSV file — sales, inventory, customer data' },
                  { icon: '💬', title: 'Ask in English', desc: 'No SQL needed — just ask questions naturally' },
                  { icon: '📊', title: 'Get Insights', desc: 'Charts, tables, and summaries generated instantly' },
                ].map((step, i) => (
                  <div key={i} className="flex gap-3 items-start">
                    <span className="text-lg flex-shrink-0 mt-0.5">{step.icon}</span>
                    <div>
                      <p className="text-xs font-semibold text-white">{step.title}</p>
                      <p className="text-xs text-slate-500 leading-relaxed">{step.desc}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Example questions */}
            <div>
              <h2 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                <span>💡</span> Example Questions
              </h2>
              <div className="space-y-2">
                {[
                  'Which product had the highest revenue?',
                  'Show me monthly sales trends',
                  'Who are my top 10 customers?',
                  'What\'s the average order value by country?',
                  'Which items are running low in stock?',
                ].map((q, i) => (
                  <div
                    key={i}
                    className="text-xs text-slate-400 px-3 py-2 rounded-lg"
                    style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.06)' }}
                  >
                    "{q}"
                  </div>
                ))}
              </div>
            </div>

            {/* Hackathon badge */}
            <div
              className="rounded-xl p-4 text-center"
              style={{ background: 'linear-gradient(135deg, rgba(0,128,255,0.15), rgba(0,87,179,0.15))', border: '1px solid rgba(0,128,255,0.3)' }}
            >
              <p className="text-xs font-bold text-do-blue mb-1">🏆 DigitalOcean Hackathon 2026</p>
              <p className="text-xs text-slate-500">Best Program for the People</p>
              <a
                href="https://digitalocean.devpost.com"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 mt-2 text-xs text-ocean-400 hover:text-ocean-300 transition-colors"
              >
                devpost.com <ExternalLink className="w-3 h-3" />
              </a>
            </div>
          </div>
        </aside>

        {/* Chat area */}
        <main className="flex-1 flex flex-col overflow-hidden">
          {/* Sidebar toggle */}
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="absolute left-0 top-1/2 -translate-y-1/2 z-10 w-5 h-12 flex items-center justify-center text-slate-500 hover:text-white transition-colors rounded-r-lg"
            style={{ background: 'rgba(255,255,255,0.08)', marginLeft: sidebarOpen ? '320px' : '0' }}
            title={sidebarOpen ? 'Hide sidebar' : 'Show sidebar'}
          >
            <span className="text-xs">{sidebarOpen ? '‹' : '›'}</span>
          </button>

          <ChatWindow
            datasetId={dataset?.dataset_id || null}
            sessionId={sessionId}
          />
        </main>
      </div>
    </div>
  )
}
