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
from dotenv import load_dotenv
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor


#Establish a connection to the Gmail IMAP server

start_time = time.time()

def read_from_bank(bank,sender_id,today_date,mail):
        print(f"Reading from {sender_id}")
        status, data = mail.search(None,f'FROM "{sender_id}"')
        
        if(status == 'OK'):
                mail_ids = data[0].split()
                if not mail_ids:
                        print(f"No new emails from {sender_id}")
                else:
                        print(f"Found {len(mail_ids)} new emails from {sender_id}")
                        #Define dataframe
                        df = pd.DataFrame(columns=['email_From','Subject','email_Date','email_body_from_html','email_body_from_plain'])

                        #Iterate through all the emails from the sender
                        for uid in mail_ids:
                                tmp_dict = {}
                                # uid = b'64523'
                                status, data = mail.fetch(uid,'(RFC822)')
                                if(status == "OK"):
                                        print(f"start processing:{uid}")
                                        msg = email.message_from_bytes(data[0][1])
                                        
                                        # Extract headers
                                        tmp_dict['email_From'] = str(make_header(decode_header(msg.get('From', '')))).replace('\r\n',' ')
                                        tmp_dict['Subject'] = str(make_header(decode_header(msg.get('Subject', '')))).replace('\r\n', ' ')
                                        tmp_dict['email_Date'] = str(make_header(decode_header(msg.get('Date', '')))).replace('\r\n', ' ')
                                        print(tmp_dict)
                                        
                                        #Extract body from mail
                                        if msg.is_multipart():
                                                for part in msg.walk():
                                                        content_type = part.get_content_type()
                                                        content_disposition = str(part.get("Content-Disposition"))
                                                        
                                                        
                                                        if(content_type =="text/plain"):
                                                                body = part.get_payload(decode=True) 
                                                                body = body.decode('utf-8',errors='ignore').strip()
                                                                body_trimmed = re.sub(r'\s+',' ',body)
                                                        
                                                                tmp_dict['email_body_from_plain'] = body_trimmed

                                                        if(content_type =="text/html"):
                                                                # print(body_trimmed)
                                                                # print(part)
                                                                body = part.get_payload(decode=True)
                                                                # Decode with proper encoding handling
                                                                try:
                                                                        body = body.decode('utf-8', errors='ignore')
                                                                except:
                                                                        body = body.decode('latin-1', errors='ignore')
                                                                soup = BeautifulSoup(body, 'html.parser')
                                                                # print(str(soup))
                                                                if(soup.body is not None):
                                                                        body_text = soup.body.get_text()
                                                                        body_trimmed = re.sub(r'\s+',' ',body_text)
                                                                else:
                                                                        body_trimmed = ""
                                                                print(body_trimmed)
                                                                tmp_dict['email_body_from_html'] = body_trimmed
                                
                                # Mark email as Seen
                                mail.store(uid, '+FLAGS', '\\Seen')
                                print(f"Marked email {uid} as Seen")
                                
                                df = pd.concat([df,pd.DataFrame([tmp_dict])], ignore_index=True)
                                print(f"Finished processing:{uid}")
                print(df.head(5))
                print("Saving as csv...")
                filename = sender_id.replace("@","__").replace(".","_")
                df.to_csv(f'D:/projects/project-quacktrack/data/ingestion/{bank}/{today_date}/{filename}_{datetime.now().strftime("%Y-%m-%d-%H-%M-%S")}.csv',index=False)
                print(f"finished procesing:{sender_id} emails.")


def get_emails(sender_config):
        load_dotenv()
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        user_email = os.getenv("GMAIL_USER")

        bank_senders = sender_config.get('id', [])
        # bank_senders = {'axis': ['alerts@axisbank.com','alerts@axis.bank.in'],'hdfc':'alerts@hdfcbank.net','icici': 'credit_cards@icicibank.com'}
        # bank_senders = ['alerts@axisbank.com'] 
        # bank_senders = ['alerts@hdfcbank.net']
        print(f"Logging in to Mailbox: {user_email}")
        try:
                ret = mail.login(user=user_email, password=os.getenv("GMAIL_APP_PASSWORD"))
                print(ret)
        except Exception as e:
                print(f"Error logging in: {e}")

        mail.select('inbox',readonly=False) #Readonly=False to mark emails as read
        #35322 total unseen emails
        
        #Fetch emails for senders in list
        key = ""
        if('axis' in bank_senders):
                key = "axis"
        if('hdfc' in bank_senders):
                key = "hdfc"
        if('icici' in bank_senders):
                key = "icici"
                        
        #Create ingestion directorys
        if key == "":
                print("No valid sender found in config")
                return "No valid sender found in config"
        else:
                today_date = datetime.now().strftime("%Y-%m-%d")
                os.makedirs(f'D:/projects/project-quacktrack/data/ingestion/{key}/{today_date}', exist_ok=True)
                read_from_bank(key,bank_senders,today_date,mail)

                print("Logging out...")
                mail.close()
                mail.logout()
                print("Logged out successfully.")
                return f"successfully processed {bank_senders} emails"

def parallelize():
        # Targets
        senders = [
                {'id': 'alerts@axisbank.com'},
                {'id': 'alerts@axis.bank.in'},
                {'id': 'alerts@hdfcbank.net'},
                {'id': 'credit_cards@icicibank.com'}
        ]
        # Execute in Parallel
        with ThreadPoolExecutor(max_workers=3) as executor:
                results = list(executor.map(get_emails, senders))

start_time = time.time()
parallelize()
end_time = time.time()

elapsed_time = end_time - start_time
print(f"Elapsed time: {elapsed_time} seconds")