import os
from pathlib import Path
from dotenv import load_dotenv
import logging
load_dotenv()

# Gmail Configuration
GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")

# Data Paths
DATA_LANDING_PATH = Path(os.getenv("DATA_LANDING_PATH"))
DATA_INGESTION_PATH = Path(os.getenv("DATA_INGESTION_PATH"))
DATA_ARCHIVE_PATH = Path(os.getenv("DATA_ARCHIVE_PATH"))
DUCKDB_PATH = os.getenv("DUCKDB_PATH")
EXTERNAL_SCHEMA = os.getenv("EXTERNAL_SCHEMA")

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Configure root logger (critical: must happen before any logger.getLogger calls)
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(),  # Output to terminal/stdout
    ],
)

logger = logging.getLogger(__name__)