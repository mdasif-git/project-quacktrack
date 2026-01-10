import imaplib
import os
import logging
import email
import quopri 
import re
import pandas as pd
import time
from email.header import decode_header, make_header



#Establish a connection to the Gmail IMAP server

start_time = time.time()
def get_emails():
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        user_email = "mdasif.uem@gmail.com"

        bank_senders = ['alerts@axis.bank.in','alerts@hdfcbank.net']
        print(f"Logging in to Mailbox: {user_email}")
        mail.login(user='mdasif.uem@gmail.com', password=os.getenv("GMAIL_APP_PASSWORD"))

        mail.select('inbox',readonly=True)
        
        
        #Fetch emails for senders in list
        for bank in bank_senders:
                print(f"Reading from {bank}")
                status, data = mail.search(None,f'FROM "{bank}"')
                
                if(status == 'OK'):
                        mail_ids = data[0].split()
                        print(len(mail_ids))
                        #Define dataframe
                        df = pd.DataFrame(columns=['From','Subject','Date','email_body'])

                        #Iterate through all the emails from the sender
                        for uid in mail_ids:
                                tmp_dict = {}
                                status, data = mail.fetch(uid,'(RFC822)')
                                if(status == "OK"):
                                        msg = email.message_from_bytes(data[0][1])
                                        #Extract body from mail
                                        if msg.is_multipart():
                                                for part in msg.walk():
                                                        content_type = part.get_content_type()
                                                        content_disposition = str(part.get("Content-Disposition"))
                                                        if(content_type =="text/plain"):
                                                                body = part.get_payload(decode=True) 
                                                                body = body.decode('utf-8',errors='ignore').strip()
                                                                body_trimmed = re.sub(r'\s+',' ',body)
                                                                tmp_dict['email_body'] = body_trimmed
                                                                #F Fetches headers only: Subject, From, Date
                                #Fetch headers: FROM, SUBJECT, DATE
                                status, data = mail.fetch(uid,'(BODY[HEADER.FIELDS (SUBJECT FROM DATE)])')
                                if(status == "OK"):
                                        split_data = data[0][1].decode('utf-8').split('\r\n')

                                        for element in split_data:
                                                if len(element.strip()) > 0:
                                                        key, value = element.split(': ')
                                                        result = {key.strip(): value.strip()}
                                                        for key,val in result.items():
                                                                tmp_dict[key] = str(make_header(decode_header(val)))

                                df = pd.concat([df,pd.DataFrame([tmp_dict])], ignore_index=True)

                        print(df.head(5))
                        print("Saving as csv...")
                        df.to_csv(f'{bank}_bank_emails.csv',index=False)

        print("Logging out...")
        mail.close()
        mail.logout()
        print("Logged out successfully.")

start_time = time.time()
get_emails()
end_time = time.time()

elapsed_time = end_time - start_time
print(f"Elapsed time: {elapsed_time} seconds")