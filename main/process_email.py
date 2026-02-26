import re
import shutil
from datetime import datetime
from pathlib import Path

import pandas as pd
import spacy
from spacy.matcher import Matcher

from config import (
    DATA_ARCHIVE_PATH,
    DATA_INGESTION_PATH,
    DATA_LANDING_PATH,
    logger,
)

# Load spacy model
nlp = spacy.load("en_core_web_sm")
matcher = Matcher(nlp.vocab)


def extract_bank_name(name):
    """Extract bank name from email sender."""
    if isinstance(name, str) and len(name) > 0:
        name_lower = name.lower()
        if "axis" in name_lower:
            return "AXIS"
        elif "hdfc" in name_lower:
            return "HDFC"
        elif "icici" in name_lower:
            return "ICICI"
    return ""
            

def extract_date(email_date):
    """Extract and parse date from email header."""
    if not email_date or not isinstance(email_date, str):
        return None

    # Remove leading/trailing whitespace and timezone abbreviations
    email_date = re.sub(r"\s*\([A-Z]{3,4}\)\s*$", "", email_date.strip())

    date_formats = [
        "%a, %d %b %Y %H:%M:%S %z",  # Fri, 17 Nov 2023 08:20:43 +0530
        "%d %b %Y %H:%M:%S %z",      # 17 Nov 2023 08:20:43 +0530
    ]

    if "GMT" in email_date:
        email_date = email_date.replace(" GMT", " +0000")

    for fmt in date_formats:
        try:
            return datetime.strptime(email_date, fmt)
        except ValueError:
            continue

    logger.error(
        f"Failed to parse date with any available format: {email_date}"
    )
    return None
def extract_transaction_type(subj):
    """Extract transaction type from subject line."""
    if isinstance(subj, str) and len(subj) > 0:
        subj_lower = subj.lower()
        if "credit" in subj_lower:
            return "CREDIT"
        elif "debit" in subj_lower:
            return "DEBIT"
    return "MISC"

def extract_transaction_details(text):
    """Extract transaction details from email body using NLP."""
    if isinstance(text, str) and len(text) > 0:
        doc = nlp(text)

        start_idx = 0
        end_idx = len(doc)

        # 1. Find the start (Greeting)
        greeting_words = {"dear", "greetings", "asif", "customer"}
        for token in doc:
            if token.text.lower() in greeting_words:
                start_idx = token.i
                break

        # 2. Find the end (Security Disclaimer)
        security_keywords = {
            "block",
            "report",
            "unauthorized",
            "signature",
            "call",
            "contact us",
        }
        for sent in doc.sents:
            if sent.start > start_idx:
                if any(key in sent.text.lower() for key in security_keywords):
                    end_idx = sent.start
                    break

        return doc[start_idx:end_idx].text.strip()
    return ""


def process_emails():
    """Process emails from landing directory to ingestion directory."""
    today_date = datetime.now().strftime("%Y-%m-%d")

    src_path = DATA_LANDING_PATH / today_date
    dest_path = DATA_INGESTION_PATH / today_date
    archive_path = DATA_ARCHIVE_PATH / today_date

    dest_path.mkdir(parents=True, exist_ok=True)
    archive_path.mkdir(parents=True, exist_ok=True)

    if not src_path.exists():
        logger.warning(f"Source path does not exist: {src_path}")
        return

    for csv_file in src_path.glob("*.csv"):
        try:
            logger.info(f"Reading: {csv_file.name}")
            df = pd.read_csv(csv_file)

            # Apply transformation functions
            df["bank"] = df["email_From"].apply(extract_bank_name)
            df["transaction_datetime"] = df["email_Date"].apply(extract_date)

            # Fill holes in the email body
            df["email_body_from_html"] = df["email_body_from_html"].fillna(
                df["email_body_from_plain"]
            )
            df["email_body_from_plain"] = df["email_body_from_plain"].fillna(
                df["email_body_from_html"]
            )

            # Extract transaction details
            df["transaction_details_from_html"] = df[
                "email_body_from_html"
            ].apply(extract_transaction_details)
            df["transaction_details_from_plain"] = df[
                "email_body_from_plain"
            ].apply(extract_transaction_details)

            # Extract transaction type
            df["transaction_type"] = df["Subject"].apply(
                extract_transaction_type
            )

            # Save processed data
            output_file = dest_path / csv_file.name
            df.to_csv(output_file, index=False)
            logger.info(f"Saved processed data to {output_file}")

            # Move original file to archive
            shutil.move(str(csv_file), str(archive_path / csv_file.name))
            logger.info(f"Archived {csv_file.name} to {archive_path}")

        except Exception as e:
            logger.error(f"Error processing {csv_file.name}: {e}")
            continue

    logger.info("Email processing completed successfully")


if __name__ == "__main__":
    process_emails()

