"""
Application configuration via environment variables.
Uses pydantic-settings for type-safe, validated config.
"""

import os
from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Paths ────────────────────────────────────────────────────────────────
    data_dir: Path = Path("data")
    packages_dir: Path = Path("../packages")

    # ── Server ───────────────────────────────────────────────────────────────
    debug: bool = True
    cors_origins: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # ── LLM Adapter (all optional — templates always work) ───────────────────
    # Set GEMINI_API_KEY to enable Gemini free-tier fallback
    gemini_api_key: str = ""
    # Set OLLAMA_URL if Ollama is running locally
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2:1b"   # 1B model for 4 GB RAM constraint
    # LLM timeout: if exceeded, circuit breaker fires and templates are used
    llm_timeout_seconds: float = 25.0

    # ── Security ─────────────────────────────────────────────────────────────
    # PIN is set by the owner at first launch, NOT stored in env
    # Vault key derived from PIN + device salt using Argon2id
    vault_salt_file: str = "vault_salt.bin"
    pin_lockout_attempts: int = 5
    pin_lockout_backoff_seconds: float = 30.0

    # ── Analytics Thresholds (matches PRD §8.1 and §8.3) ────────────────────
    completeness_block_threshold: float = 0.6   # Below → escalate
    completeness_caveat_threshold: float = 0.8  # 0.6–0.8 → proceed with caveat
    day_coverage_block: float = 0.70            # Below 70% → BLOCK
    day_coverage_warn: float = 0.85             # 70–85% → WARN

    # ── Outbox (cloud sync) ───────────────────────────────────────────────────
    cloud_api_url: str = "http://localhost:9000/v1/aggregates"
    outbox_retry_backoff_seconds: float = 30.0
    outbox_max_attempts: int = 10

    # ── Rule Pack ────────────────────────────────────────────────────────────
    rules_version: str = "v1"
    notice_version: str = "v1"


@lru_cache
def get_settings() -> Settings:
    return Settings()
