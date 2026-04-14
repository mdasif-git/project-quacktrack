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


# Define your templates
BANK_CONFIGS = {
    "AXIS": [
        {
            "trigger": lambda text: "Credit Card Transaction" in text,
            "category": "DEBIT",
            "sub_type": "CREDIT CARD",
            "pattern": r"Transaction Amount:\s*INR\s*(?P<amount>[\d,.]+)\s*Merchant Name:\s*(?P<info>.*?)\s*Axis Bank"
        },
        {
            "trigger": lambda text: "has been debited" in text,
            "category": "DEBIT",
            "sub_type": "BANK",
            "pattern": r"debited with INR\s*(?P<amount>[\d,.]+)\s*on\s*[\d\-\s:]+IST\s*by\s*(?P<info>.+?)\.*$"
        },
        {
            "trigger": lambda text: "XX1424 has been credited" in text,
            "category": "CREDIT",
            "sub_type": "BANK",
            "pattern": r"credited with INR\s*(?P<amount>[\d,.]+)\s*on\s*[\d\-\s:]+IST\s*by\s*(?P<info>.+?)\.*$"
        },
        {
            "trigger" : lambda text: "Thank you for using your credit card no. XX4017" in text,
            "category" : "DEBIT",
            "sub_type" : "CREDIT CARD",
            "pattern" : r"for INR\s*(?P<amount>[\d,.]+)\s*at\s*(?P<info>.+?)\s*on\s*(\d{2}-\d{2}-\d{4}\s*\d{2}:\d{2}:\d{2})"
        },
        {
            "trigger": lambda text: "UPI" in text and "Debited" in text,
            "category": "DEBIT",
            "sub_type": "UPI",
            "pattern": r"Amount Debited:\s*INR\s*(?P<amount>[\d,.]+).*?Transaction Info:\s*(?P<info>.*)"
        },
        {
            "trigger": lambda text: "AUTOPAY" in text or "debited with" in text,
            "category": "DEBIT",
            "sub_type": "AUTOPAY",
            "pattern": r"debited with\s*INR\s*(?P<amount>[\d,.]+).*?by\s*(?P<info>.*?)\.To check"
        },
        {
            "trigger": lambda text: "credited with" in text,
            "category": "CREDIT",
            "sub_type": "NULL",
            "pattern": r"credited with\s*INR\s*(?P<amount>[\d,.]+).*?by\s*(?P<info>.*?)\.\s*To check"
        }
    ],
    "HDFC" : [
        {
            "trigger" : lambda text : "has been debited" in text,
            "category" : "DEBIT",
            "sub_type" : "BANK",
            "pattern" : r"Rs\.(?P<amount>[\d,.]+)\s*has been debited from account\s*[\*]*\s*\d+\s*(?P<info>.+?)\s*on\s*[\d\-]+"
        },
        {
            "trigger" : lambda text : "is successfully credited" in text,
            "category" : "CREDIT",
            "sub_type" : "BANK",
            "pattern" : r"Rs\.\s*(?P<amount>[\d,.]+)\s*is successfully credited to your account\s*[\*]*\s*\d+\s*(?P<info>.+?)\s*on\s*[\d\-]+"
        },
        {
            "trigger" : lambda text : "Thank you for using your HDFC Bank Credit Card" in text,
            "category" : "DEBIT",
            "sub_type" : "CREDIT CARD",
            "pattern" : r"Credit Card ending\s*\d+\s*for Rs\s*(?P<amount>[\d,.]+)\s*at\s*(?P<info>.+?)\s*on\s*[\d\-]+"
        },
        {
            "trigger" : lambda text : "Thank you for using your HDFC Bank Debit Card" in text,
            "category" : "DEBIT",
            "sub_type" : "DEBIT CARD",
            "pattern" : r"Debit Card ending\s*\d+\s*(?:for ATM withdrawal\s*)?for Rs\s*(?P<amount>[\d,.]+)\s*(?:in\s*\w+\s*)?at\s*(?P<info>.+?)\s*on\s*[\d\-]+"
        }
        
    ],
    "ICICI" : [
        {
            "trigger" : lambda text : "Your ICICI Bank Credit Card XX3008 has been used for a transaction" in text,
            "category" : "DEBIT",
            "sub_type" : "CREDIT CARD",
            "pattern" : r"transaction of INR\s*(?P<amount>[\d,.]+)\s*on\s*.+?(?:;|at)\s*[\d:]+\.\s*Info:\s*(?P<info>.+?)\."
        }
    ]
}

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