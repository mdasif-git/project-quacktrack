## V2 version: To read from different mail sender: -- MD ASIF
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

        bank_senders = ['alerts@hdfcbank.net']
        print(f"Logging in to Mailbox: {user_email}")
        mail.login(user='mdasif.uem@gmail.com', password=os.getenv("GMAIL_APP_PASSWORD"))

        mail.select('inbox',readonly=True)
        
        
        #Fetch emails for senders in list
        for bank in bank_senders:
                print(f"Reading from {bank}")
                status, inbox_data = mail.search(None,f'FROM "{bank}"')
                
                if(status == 'OK'):
                        mail_ids = inbox_data[0].split()
                        print(len(mail_ids))
                        #Define dataframe
                        df = pd.DataFrame(columns=['From','Subject','Date','email_body'])

                        #Iterate through all the emails from the sender
                        # for uid in mail_ids:
                        tmp_dict = {}
                        status, data = mail.fetch(mail_ids[-1],'(RFC822)')
                        print("Fetch status:",status)
                        if(status == "OK"):
                                msg = email.message_from_bytes(data[0][1])
                                #Extract body from mail
                                print(msg.is_multipart())

                                if msg.is_multipart():
                                        for part in msg.walk():
                                                content_type = part.get_content_type()
                                                print(content_type)
                                                content_disposition = str(part.get("Content-Disposition"))
                                                if(content_type =="text/html"):
                                                        body = part.get_payload(decode=True) 
                                                        body = body.decode('utf-8',errors='ignore').strip()
                                                        body_trimmed = re.sub(r'\s+',' ',body)
                                                        print(body_trimmed)
                                                        tmp_dict['email_body'] = body_trimmed
                                
                                #Fetch headers: FROM, SUBJECT, DATE
                        #         status, data = mail.fetch(uid,'(BODY[HEADER.FIELDS (SUBJECT FROM DATE)])')
                        #         if(status == "OK"):
                        #                 split_data = data[0][1].decode('utf-8').split('\r\n')
                        #                 print(split_data)
                        #                 for element in split_data:
                        #                         if len(element.strip()) > 0 and (":" in element.strip()):
                                                        
                        #                                 key, value = element.split(':',1)
                        #                                 result = {key.strip(): value.strip()}
                        #                                 for key,val in result.items():
                        #                                         # Conditional decoding for headers
                        #                                         decoded_parts = decode_header(val)
                        #                                         if any(enc for _, enc in decoded_parts if enc):
                        #                                                 val = str(make_header(decode_header(val)))
                        #                                         print("key:",key,"val:",val)
                        #                                         tmp_dict[key] = val

                        #         df = pd.concat([df,pd.DataFrame([tmp_dict])], ignore_index=True)

                        # print(df.head(5))
                        # print("Saving as csv...")
                        # df.to_csv(f'{bank}_bank_emails.csv',index=False)

        print("Logging out...")
        mail.close()
        mail.logout()
        print("Logged out successfully.")

start_time = time.time()
get_emails()
end_time = time.time()

elapsed_time = end_time - start_time
print(f"Elapsed time: {elapsed_time} seconds")