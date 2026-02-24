# 🎣 Gradient Fisherman

**SMB Data Assistant** — Ask your business data questions in plain English. Get instant charts and insights.

Built for the **DigitalOcean Gradient™ AI Hackathon** — *Best Program for the People* category.

> Powered by **DigitalOcean Gradient™ AI** with **Claude Sonnet 4.6**

---

## The Problem

Small business owners drown in spreadsheets. They can't afford a data analyst. They don't know SQL. They just want answers: *"What were my top 5 products last month?"* or *"Which customers haven't ordered in 90 days?"*

## The Solution

Upload your CSV → Ask questions in plain English → Get instant charts and summaries.

No SQL. No formulas. No analyst needed.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Next.js Frontend                      │
│   File Upload ──► Chat Interface ──► Chart Renderer      │
│                                      (Recharts)          │
└───────────────────────┬─────────────────────────────────┘
                        │ REST API
┌───────────────────────▼─────────────────────────────────┐
│               FastAPI Backend  (Python / uv)             │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │ Ingest Agent │  │ Query Agent  │  │   Viz Agent   │  │
│  │ CSV parsing  │  │ NL → pandas  │  │ Chart configs │  │
│  │ schema infer │  │ via Gradient │  │ (Recharts)    │  │
│  └──────────────┘  └──────┬───────┘  └───────────────┘  │
└─────────────────────────  │  ───────────────────────────┘
                            │
            ┌───────────────▼────────────────┐
            │  DigitalOcean Gradient™ AI      │
            │  Claude Sonnet 4.6 (inference)  │
            └────────────────────────────────┘
```

### Agent Roles

| Agent | Responsibility |
|-------|---------------|
| **Ingest Agent** | Parse CSV, infer column types (numeric/categorical/datetime/text), generate data profile for LLM context |
| **Query Agent** | Translate natural language → safe pandas expression via Claude Sonnet 4.6 on Gradient AI; execute in sandboxed namespace |
| **Viz Agent** | Select best chart type from query result shape; emit Recharts-compatible config |

---

## Stack

| Layer | Technology |
|-------|-----------|
| AI Inference | DigitalOcean Gradient™ AI — Claude Sonnet 4.6 |
| Backend | Python 3.12 · FastAPI · uv · pandas |
| Frontend | Next.js 14 · TypeScript · Tailwind CSS · Recharts |
| Deploy | Vercel (frontend) · Railway / DO App Platform (backend) |

---

## Quick Start

### Prerequisites
- DigitalOcean account with a **Gradient AI Model Access Key**
- Node.js 18+ and Python 3.12+ with `uv`

### Backend

```bash
cd backend
uv sync
cp .env.example .env
# Set GRADIENT_API_KEY in .env
uv run uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env.local
# Set NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev
```

---

## Environment Variables

**`backend/.env`**
```
GRADIENT_API_KEY=your_do_gradient_model_access_key
GRADIENT_BASE_URL=https://inference.do-ai.run/v1
GRADIENT_MODEL=claude-sonnet-4-6
```

**`frontend/.env.local`**
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## Hackathon Submission

- **Event:** DigitalOcean Gradient™ AI Hackathon
- **Category:** Best Program for the People
- **Devpost:** https://digitalocean.devpost.com
- **Deadline:** March 18, 2026

## License

MIT
