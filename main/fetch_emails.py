import imaplib
import os
import logging
import email
import quopri 
import re

from email.header import decode_header, make_header

#Establish a connection to the Gmail IMAP server

mail = imaplib.IMAP4_SSL("imap.gmail.com")
user_email = "mdasif.uem@gmail.com"

bank_senders = ['alerts@axis.bank.in']
print(f"Logging in to Mailbox: {user_email}")
mail.login(user='mdasif.uem@gmail.com', password=os.getenv("GMAIL_APP_PASSWORD"))

mail.select('inbox',readonly=True)
status, data = mail.search(None,f'FROM "{bank_senders[0]}"')

mail_ids = data[0].split()
print(len(mail_ids))
# status, data = mail.fetch(mail_ids[-1],'(RFC822)')
status, data = mail.fetch(mail_ids[-1],'(RFC822)')
msg = email.message_from_bytes(data[0][1])
# print(msg)
if msg.is_multipart():
        for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                if(content_type =="text/plain"):
                        body = part.get_payload(decode=True) 
                        body = body.decode('utf-8',errors='ignore').strip()
                        body_trimmed = re.sub(r'\s+',' ',body)
                        print(body_trimmed)
#F Fetches headers only: Subject, From, Date
status, data = mail.fetch(mail_ids[-1],'(BODY[HEADER.FIELDS (SUBJECT FROM DATE)])')
print("Status: ", status)
print("Data type: ", data)
#1: first technique to decode email parts 
# decoded_parts = decode_header(data)
print(type(data))
print(len(data))
print(data[0][1])
print("decoded data: ", data[0][1].decode('utf-8'))
split_data = data[0][1].decode('utf-8').split('\r\n')
print(split_data)
for element in split_data:
        if len(element.strip()) > 0:
                key, value = element.split(': ')
                result = {key.strip(): value.strip()}
                print(result)
                print("Clean version:")
                for key,val in result.items():
                        print(str(make_header(decode_header(val))))
                # print(str(make_header(decode_header(result['Date']))))
                print("===")
# print("First element: ",data[0])
# print("Second element: ", data[1])
# print(data[0][1])

raw_email_string = data[0][1].decode('utf-8')
# print("Decoded string: ", data[0][1].decode('utf-8'))

email_message = email.message_from_string(raw_email_string)
# print(email_message)
# print(email_message.is_multipart())
# with open("email_parts.txt","w") as f:
#     for part in email_message.walk():
#         f.write("***Begin of new part***\n")
#         f.write(str(part))
#         f.write("\n***End of part***\n\n\n")
# with open("email_payload.txt","w") as f:
# for part in email_message.walk():
#     if(part.is_multipart()):
#         print("Keys: ",part.keys())
#         print(f"Content type: {part.get_content_type()}")
#         print(f"Content main type: {part.get_content_maintype()}")
#         print(f"Content sub type: {part.get_content_subtype()}")
#         print(f"is multipart: {part.is_multipart()}")
#     # print(part.get_payload(decode=True))
#         print(f"Attachment filename: {part.get_filename()}")
#         print(f"Sender: {part.get("From")}")
#         print(f"Decoded Sender name: {email.header.decode_header(part.get("From"))}")
#         print(f"Subject: {part.get("Subject")}")
#         print(f"Decoded Subject: {email.header.decode_header(part.get("Subject"))}")
#         print(f"To: {part.get("To")}")
#         print(f"Date: {part.get("Date")}")
#         print(f"Timestamp: {part.get("Timestamp")}")
#         print("---------------------------------------------------")
        # f.write("\n***Begin of new part***\n")
        # f.write("\nContent type: " + part.get_content_type())
        # f.write("\nIs Multipart: " + str(part.is_multipart()))
        # f.write("\nContent Disposition: " + str(part.get("Content-Disposition")))
        # if not part.is_multipart():
        #     payload = part.get_payload(decode=True)
        #     if payload:
        #         f.write("\nPayload: " + str(quopri.decodestring(payload).decode('utf-8', errors='ignore')))
        # f.write("\n***End of part***")

        # f.write("\n\n\n")
# for idx, body in email_message.items():
#     print(f"{idx}::: {body}")
#     print("\n\n\n")
#     print("---------------------------------------------------")
print("Logging out...")
mail.close()
mail.logout()
print("Logged out successfully.")
# mail.fetch(dta[-1], '(RFC822)')
