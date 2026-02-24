"""
Gradient Fisherman — FastAPI Backend
AI-powered SMB data assistant using DigitalOcean Gradient™ AI
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import upload, chat

app = FastAPI(
    title="Gradient Fisherman API",
    description="AI-powered data assistant for SMBs — powered by DigitalOcean Gradient™ AI",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
cors_origins = [o.strip() for o in settings.CORS_ORIGINS.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(upload.router)
app.include_router(chat.router)


@app.get("/")
async def root():
    return {
        "service": "Gradient Fisherman",
        "description": "AI-powered data assistant for SMBs",
        "powered_by": "DigitalOcean Gradient™ AI",
        "docs": "/docs",
    }
