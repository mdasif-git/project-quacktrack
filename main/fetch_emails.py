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


#Establish a connection to the Gmail IMAP server

start_time = time.time()
def get_emails():
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        user_email = "mdasif.uem@gmail.com"

        bank_senders = ['credit_cards@icicibank.com']
        # bank_senders = ['alerts@axis.bank.in'] 
        # bank_senders = ['alerts@hdfcbank.net']
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
                        df = pd.DataFrame(columns=['From','Subject','Date','email_body_from_html','email_body_from_plain'])

                        #Iterate through all the emails from the sender
                        for uid in mail_ids:
                                tmp_dict = {}
                                # uid = b'64523'
                                status, data = mail.fetch(uid,'(RFC822)')
                                if(status == "OK"):
                                        print(f"start processing:{uid}")
                                        msg = email.message_from_bytes(data[0][1])
                                        
                                        # Extract headers
                                        tmp_dict['From'] = str(make_header(decode_header(msg.get('From', '')))).replace('\r\n',' ')
                                        tmp_dict['Subject'] = str(make_header(decode_header(msg.get('Subject', '')))).replace('\r\n', ' ')
                                        tmp_dict['Date'] = str(make_header(decode_header(msg.get('Date', '')))).replace('\r\n', ' ')
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

                                                                # body_trimmed = ""        
                                                                tmp_dict['email_body_from_html'] = body_trimmed
                                                                
                                                                # Extract the main text content (assuming it's in the specific <td> class)
                                                                # main_text = ""
                                                                # main_td = soup.find('td', class_='esd-text')
                                                                # if main_td:
                                                                #         main_text = main_td.get_text(separator=' ', strip=True)
                                                                #         print(main_text)
                                                                # tmp_dict['email_body'] = main_text
                                #F Fetches headers only: Subject, From, Date
                                #Fetch headers: FROM, SUBJECT, DATE
                                # status, data = mail.fetch(uid,'(BODY[HEADER.FIELDS (SUBJECT FROM DATE)])')
                                # if(status == "OK"):
                                #         split_data = data[0][1].decode('utf-8').split('\r\n')

                                #         for element in split_data:
                                #                 if len(element.strip()) > 0 and element.strip().find(":") != -1:
                                #                         # print(element.split(':',1))
                                #                         # print(f"element: {element} in split_data : {split_data}")

                                #                         key, value = (element.replace('\n',' ')).split(':',1)
                                #                         result = {key.strip(): value.strip()}
                                #                         for key,val in result.items():
                                #                                 tmp_dict[key] = str(make_header(decode_header(val)))

                                df = pd.concat([df,pd.DataFrame([tmp_dict])], ignore_index=True)
                                print(f"Finished processing:{uid}")
                print(df.head(5))
                print("Saving as csv...")
                df.to_csv(f'{bank}_bank_emails.csv',index=False)
                print(f"finished procesing:{bank} emails.")


        print("Logging out...")
        mail.close()
        mail.logout()
        print("Logged out successfully.")

start_time = time.time()
get_emails()
end_time = time.time()

elapsed_time = end_time - start_time
print(f"Elapsed time: {elapsed_time} seconds")