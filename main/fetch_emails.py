import imaplib
import os
import logging
import email
import quopri 

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
status, data = mail.fetch(mail_ids[-1],'(RFC822)')
print(len(data))
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
for part in email_message.walk():
    print("Keys: ",part.keys())
    print(f"Content type: {part.get_content_type()}")
    print(f"Content main type: {part.get_content_maintype()}")
    print(f"Content sub type: {part.get_content_subtype()}")
    print(f"is multipart: {part.is_multipart()}")
    # print(part.get_payload(decode=True))
    print(f"Attachment filename: {part.get_filename()}")
    print(f"Sender: {part.get("From")}")
    print(f"Decoded Sender name: {email.header.decode_header(part.get("From"))}")
    print(f"Subject: {part.get("Subject")}")
    print(f"Decoded Subject: {email.header.decode_header(part.get("Subject"))}")
    print(f"To: {part.get("To")}")
    print(f"Date: {part.get("Date")}")
    print(f"Timestamp: {part.get("Timestamp")}")
    print("---------------------------------------------------")
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
