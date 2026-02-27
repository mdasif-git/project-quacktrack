import imaplib
import os
import logging
import email
import re
import pandas as pd
import time
from email.header import decode_header, make_header
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
import duckdb

from config import (
    DATA_LANDING_PATH,
    DATA_INGESTION_PATH,
    DATA_ARCHIVE_PATH,
    DUCKDB_PATH,
    logger
)



def get_last_processed(sender_id):
    """Get the last processed transaction date for a bank."""
    with duckdb.connect(DUCKDB_PATH) as conn:
        query = f"SELECT CAST(MAX(transaction_datetime) as date) as max_date FROM transactions_external WHERE bank='{sender_id}'"
        result = conn.execute(query).fetchone()
    if result and result[0]:
        return result[0]
    else:
        return None


def read_from_bank(bank, sender_id, file_path, mail, last_processed=None):
    """Read emails from a specific bank sender."""
    logger.info(f"Reading from {sender_id}")
    if last_processed is not None:
        date_days_ago = last_processed.strftime("%d-%b-%Y")
        search_criteria = f'FROM "{sender_id}" SINCE {date_days_ago}'
    else:
        search_criteria = f'UNSEEN FROM "{sender_id}"'

    logger.info(f"Searching with criteria: {search_criteria}")
    status, data = mail.search(None, search_criteria)

    if status == "OK":
        mail_ids = data[0].split()
        df = pd.DataFrame(
            columns=[
                "email_Message_id",
                "email_From",
                "Subject",
                "email_Date",
                "email_body_from_html",
                "email_body_from_plain",
            ]
        )
        if not mail_ids:
            return f"No new emails from {sender_id}"
        else:
            logger.info(f"Found {len(mail_ids)} new emails from {sender_id}")

            # Iterate through all the emails from the sender
            for uid in mail_ids:
                tmp_dict = {}
                status, data = mail.fetch(uid, "(RFC822)")
                if status == "OK":
                    logger.info(f"Start processing: {uid}")
                    msg = email.message_from_bytes(data[0][1])

                    # Extract headers
                    tmp_dict["email_Message_id"] = msg["Message-ID"]
                    tmp_dict["email_From"] = str(
                        make_header(decode_header(msg.get("From", "")))
                    ).replace("\r\n", " ")
                    tmp_dict["Subject"] = str(
                        make_header(decode_header(msg.get("Subject", "")))
                    ).replace("\r\n", " ")
                    tmp_dict["email_Date"] = str(
                        make_header(decode_header(msg.get("Date", "")))
                    ).replace("\r\n", " ")

                    # Extract body from mail
                    if msg.is_multipart():
                        for part in msg.walk():
                            content_type = part.get_content_type()
                            content_disposition = str(
                                part.get("Content-Disposition")
                            )

                            if content_type == "text/plain":
                                body = part.get_payload(decode=True)
                                body = body.decode("utf-8", errors="ignore").strip()
                                body_trimmed = re.sub(r"\s+", " ", body)
                                tmp_dict["email_body_from_plain"] = body_trimmed

                            if content_type == "text/html":
                                body = part.get_payload(decode=True)
                                # Decode with proper encoding handling
                                try:
                                    body = body.decode("utf-8", errors="ignore")
                                except Exception:
                                    body = body.decode("latin-1", errors="ignore")
                                soup = BeautifulSoup(body, "html.parser")
                                if soup.body is not None:
                                    body_text = soup.body.get_text()
                                    body_trimmed = re.sub(r"\s+", " ", body_text)
                                else:
                                    body_text = soup.get_text(
                                        separator=" ", strip=True
                                    )
                                    body_trimmed = re.sub(r"\s+", " ", body_text)
                                tmp_dict["email_body_from_html"] = body_trimmed

                    # Mark email as Seen
                    mail.store(uid, "+FLAGS", "\\Seen")
                    logger.info(f"Marked email {uid} as Seen")

                    df = pd.concat([df, pd.DataFrame([tmp_dict])], ignore_index=True)
                    logger.info(f"Finished processing: {uid}")

            logger.info(df.head(5))
            logger.info("Saving as CSV...")
            filename = sender_id.replace("@", "__").replace(".", "_")
            df.to_csv(
                f"{file_path}/{filename}_{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}.csv",
                index=False,
            )
            return f"Finished processing: {sender_id} emails."


def get_emails(sender_config):
    """Fetch emails from Gmail for a specific bank."""
    load_dotenv()
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    user_email = os.getenv("GMAIL_USER")

    bank_senders = sender_config.get("id", [])
    bank_name = sender_config.get("bank", [])
    logger.info(f"Bank: {bank_name}")
    last_fetched_date = get_last_processed(bank_name)
    logger.info(f"Last fetched date for {bank_name} is {last_fetched_date}")

    logger.info(f"Logging in to Mailbox: {user_email}")
    try:
        ret = mail.login(user=user_email, password=os.getenv("GMAIL_APP_PASSWORD"))
    except Exception as e:
        logger.error(f"Error logging in: {e}")

    mail.select("inbox", readonly=False)  # readonly=False to mark emails as read

    # Fetch emails for senders in list
    key = ""
    if "axis" in bank_senders:
        key = "axis"
    if "hdfc" in bank_senders:
        key = "hdfc"
    if "icici" in bank_senders:
        key = "icici"

    # Create ingestion directories
    if key == "":
        logger.warning("No valid sender found in config")
        return "No valid sender found in config"
    else:
        today_date = datetime.now().strftime("%Y-%m-%d")
        file_path = f"{DATA_LANDING_PATH}/{today_date}"
        os.makedirs(file_path, exist_ok=True)
        logger.info(read_from_bank(key, bank_senders, file_path, mail, last_fetched_date))

        logger.info("Logging out...")
        mail.close()
        mail.logout()
        logger.info("Logged out successfully.")
        return f"Successfully processed {bank_senders} emails"

def parallelize():
    """Execute email fetching in parallel for multiple banks."""
    # Targets
    senders = [
        {"id": "alerts@axisbank.com", "bank": "AXIS"},
        {"id": "alerts@axis.bank.in", "bank": "AXIS"},
        {"id": "alerts@hdfcbank.net", "bank": "HDFC"},
        {"id": "credit_cards@icicibank.com", "bank": "ICICI"},
    ]
    # Execute in Parallel
    with ThreadPoolExecutor(max_workers=3) as executor:
        results = list(executor.map(get_emails, senders))


if __name__ == "__main__":
    start_time = time.time()
    parallelize()
    end_time = time.time()

    elapsed_time = end_time - start_time
    logger.info(f"Elapsed time: {elapsed_time} seconds")