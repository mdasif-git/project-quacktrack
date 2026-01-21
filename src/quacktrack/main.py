"""Main entry point for QuackTrack."""

import logging
import imaplib
import os
import logging
import email
import quopri 
import re
import pandas as pd
import time
from email.header import decode_header, make_header
from bs4 import BeautifulSoup
from quacktrack.config import config

# Configure logging
logging.basicConfig(level=config.LOG_LEVEL)
logger = logging.getLogger(__name__)


def main():
    """Main function."""
    logger.info("Starting QuackTrack...")

    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    user_email = "mdasif.uem@gmail.com"

    bank_senders = ["alerts@axis.bank.in", "credit_cards@icicibank.com", "alerts@hdfcbank.net"]
    print(f"Logging in to Mailbox: {user_email}")
    mail.login(user="mdasif.uem@gmail.com", password=os.getenv("GMAIL_APP_PASSWORD"))

    mail.select("inbox", readonly=True)

    # Fetch emails for senders in list
    for bank in bank_senders:
        print(f"Reading from {bank}")
        status, data = mail.search(None, f'FROM "{bank}"')

        if status == "OK":
            mail_ids = data[0].split()
            print(len(mail_ids))
            # Define dataframe
            df = pd.DataFrame(columns=["From", "Subject", "Date", "email_body_from_html", "email_body_from_plain"])

            # Iterate through all the emails from the sender
            for uid in mail_ids:
                tmp_dict = {}
                # uid = b'64523'
                status, data = mail.fetch(uid, "(RFC822)")
                if status == "OK":
                    print(f"start processing:{uid}")
                    msg = email.message_from_bytes(data[0][1])

                    # Extract headers
                    tmp_dict["From"] = str(make_header(decode_header(msg.get("From", "")))).replace("\r\n", " ")
                    tmp_dict["Subject"] = str(make_header(decode_header(msg.get("Subject", "")))).replace("\r\n", " ")
                    tmp_dict["Date"] = str(make_header(decode_header(msg.get("Date", "")))).replace("\r\n", " ")
                    print(tmp_dict)

                    # Extract body from mail
                    if msg.is_multipart():
                        for part in msg.walk():
                            content_type = part.get_content_type()
                            content_disposition = str(part.get("Content-Disposition"))

                            if content_type == "text/plain":
                                body = part.get_payload(decode=True)
                                body = body.decode("utf-8", errors="ignore").strip()
                                body_trimmed = re.sub(r"\s+", " ", body)

                                tmp_dict["email_body_from_plain"] = body_trimmed

                            if content_type == "text/html":
                                # print(body_trimmed)
                                # print(part)
                                body = part.get_payload(decode=True)
                                # Decode with proper encoding handling
                                try:
                                    body = body.decode("utf-8", errors="ignore")
                                except:
                                    body = body.decode("latin-1", errors="ignore")
                                soup = BeautifulSoup(body, "html.parser")
                                # print(str(soup))
                                if soup.body is not None:
                                    body_text = soup.body.get_text()
                                    body_trimmed = re.sub(r"\s+", " ", body_text)
                                else:
                                    body_trimmed = ""
                                print(body_trimmed)

                                # body_trimmed = ""
                                tmp_dict["email_body_from_html"] = body_trimmed

                df = pd.concat([df, pd.DataFrame([tmp_dict])], ignore_index=True)
                print(f"Finished processing:{uid}")
        print(df.head(5))
        print("Saving as csv...")
        df.to_csv(f"{bank}_bank_emails.csv", index=False)
        print(f"finished procesing:{bank} emails.")

    print("Logging out...")
    mail.close()
    mail.logout()
    print("Logged out successfully.")

    logger.info("QuackTrack completed!")


if __name__ == "__main__":
    start_time = time.time()
    main()
    end_time = time.time()
    elapsed_time = end_time - start_time
    logger.info(f"Elapsed time: {elapsed_time} seconds")
