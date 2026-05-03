import re
import shutil
from datetime import datetime
from pathlib import Path

import pandas as pd


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

    # Note: Logger not available in this helper function, date parsing will silently fail
    # If full logging needed, pass context as parameter and use context.log.error()
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

def extract_transaction_details(text, nlp_model):
    if isinstance(text, str) and len(text) > 0:
        doc = nlp_model(text)
        start_idx = 0
        end_idx = len(doc)

        # 1. Find the start (Greeting)
        greeting_words = {"dear", "greetings", "asif", "customer"}
        for token in doc:
            if token.text.lower() in greeting_words:
                start_idx = token.i
                break

        # 2. Find the end — search by token position, not sentence boundary
        security_keywords = {
            "if this transaction was not initiated by you",
            "to block upi",
            "unauthorized",
            "call us at",
            "regards",
            "sms blockupi",
            "available balance",
            "to check your"
        }

        full_text_lower = doc.text.lower()
        earliest_cut = len(doc.text)  # track the earliest keyword hit

        for key in security_keywords:
            pos = full_text_lower.find(key)
            if pos != -1 and pos < earliest_cut:
                earliest_cut = pos

        # Convert character position → token index
        if earliest_cut < len(doc.text):
            for token in doc:
                if token.idx >= earliest_cut:
                    end_idx = token.i
                    break

        return doc[start_idx:end_idx].text.strip()
    return "" 

def first_parse_transaction_email_u_regex(bank_name, text, bank_configs): 
    rules = bank_configs.get(bank_name, []) 
    for rule in rules:
        # Check if this rule matches the email content
        if rule["trigger"](text):
            match = re.search(rule["pattern"], text, re.DOTALL | re.IGNORECASE)
            if match:
                return {
                    "BANK": bank_name,
                    "CATEGORY": rule["category"],
                    "SUB_TYPE": rule["sub_type"],
                    "AMOUNT": match.group("amount").strip(),
                    "INFO": match.group("info").strip()
                }
            return ("pattern mismatch")
    return None # Return None if no rules match


def process_email_from_file(context, src_file_path, data_ingestion_path, data_archive_path, bank_configs, nlp_model, target_date):
    """Process emails from landing directory to ingestion directory."""
    today_date = datetime.now().strftime("%Y-%m-%d")

    # src_path = DATA_LANDING_PATH / today_date
    dest_path = data_ingestion_path / target_date
    archive_path = data_archive_path / target_date

    dest_path.mkdir(parents=True, exist_ok=True)
    archive_path.mkdir(parents=True, exist_ok=True)

    # if not src_path.exists():
    #     context.log.warning(f"Source path does not exist: {src_path}")
    #     return

    # for csv_file in src_path.glob("*.csv"):
    try:
        context.log.info(f"Reading: {src_file_path}")
        df = pd.read_csv(src_file_path)

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
        ].apply(lambda x: extract_transaction_details(x, nlp_model))
        df["transaction_details_from_plain"] = df[
            "email_body_from_plain"
        ].apply(lambda x: extract_transaction_details(x, nlp_model))

        # Extract transaction type
        df["transaction_type"] = df["Subject"].apply(
            extract_transaction_type
        )

        # First Pass - use regex to parse transaction details for known patterns
        # Pass bank_configs to the regex parser
        df['transaction_detail_regex_extracted'] = df.apply(
            lambda row: first_parse_transaction_email_u_regex(row['bank'], row['transaction_details_from_plain'], bank_configs),
            axis=1
        )


        # Save processed data
        file_name = src_file_path.split('/')[-1]
        output_file = dest_path / file_name
        df.to_csv(output_file, index=False)
        context.log.info(f"Saved processed data to {output_file}")

        # Move original file to archive
        shutil.move(str(src_file_path), str(archive_path / file_name))
        context.log.info(f"Archived {file_name} to {archive_path}")
        return output_file
    except Exception as e:
        context.log.error(f"Error processing {src_file_path}: {e}")

    context.log.info("Email processing completed successfully")


