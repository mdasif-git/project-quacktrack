"""Configuration management for QuackTrack."""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Application configuration."""

    # Gmail
    GMAIL_USER = os.getenv("GMAIL_USER")
    GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")

    # Database
    DUCKDB_PATH = os.getenv("DUCKDB_PATH", "./data/bank_statements.duckdb")

    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    # Paths
    PROJECT_ROOT = Path(__file__).parent.parent.parent
    DATA_DIR = PROJECT_ROOT / "data"


config = Config()
