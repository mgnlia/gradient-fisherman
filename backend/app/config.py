"""Configuration and Gradient™ AI client setup."""
import os
from functools import lru_cache
from openai import OpenAI
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # DigitalOcean Gradient™ AI
    GRADIENT_API_KEY: str = ""
    GRADIENT_BASE_URL: str = "https://inference.do-ai.run/v1"
    GRADIENT_MODEL: str = "llama3.1-70b-instruct"
    
    # App settings
    APP_ENV: str = "development"
    CORS_ORIGINS: str = "http://localhost:3000,https://*.vercel.app"
    MAX_FILE_SIZE_MB: int = 10
    
    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()


def get_gradient_client() -> OpenAI:
    """
    Returns an OpenAI-compatible client pointed at DigitalOcean Gradient™ AI.
    The Gradient™ AI platform is fully OpenAI SDK compatible.
    """
    api_key = settings.GRADIENT_API_KEY
    if not api_key:
        raise ValueError(
            "GRADIENT_API_KEY not set. Please add your DigitalOcean Gradient™ AI key to .env"
        )
    
    return OpenAI(
        api_key=api_key,
        base_url=settings.GRADIENT_BASE_URL,
    )
