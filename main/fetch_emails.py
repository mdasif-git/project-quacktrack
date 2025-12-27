import imaplib
import os
import logging
import email
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
print(email_message.is_multipart())
for part in email_message.walk():
    print(part)
    print("---------------------------------------------------")
# for idx, body in email_message.items():
#     print(f"{idx}::: {body}")
#     print("\n\n\n")
#     print("---------------------------------------------------")
print("Logging out...")
mail.close()
mail.logout()
print("Logged out successfully.")
# mail.fetch(dta[-1], '(RFC822)')
