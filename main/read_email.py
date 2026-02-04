import duckdb


bank_senders = ['alerts@axis.bank.in','alerts@hdfcbank.net','credit_cards@icicibank.com']

with duckdb.connect("D:/projects/project-quacktrack/data/duck_db/daily_transactions.db") as conn:
    conn.sql("CREATE TABLE IF NOT EXISTS bank_emails (email_from VARCHAR,subject VARCHAR, email_date VARCHAR, email_body_html VARCHAR, email_body_plain VARCHAR, ingestion_date timestamp)")

    for bank in bank_senders:
        filename = bank.replace("@","__").replace(".","_")
        print(f"Processing file: {filename}.csv")
        conn.read_csv(f"{filename}.csv")
        conn.sql(f"Select count(*) as total_emails from {filename}.csv")
        conn.sql(f"INSERT INTO bank_emails (SELECT email_From, Subject, email_Date, email_body_from_html,email_body_from_plain, CURRENT_localtimestamp() FROM {filename}.csv)")
        conn.table("bank_emails").show()
        print(f"Processed and inserted {filename} into table")
    
    conn.sql("Select distinct email_from from bank_emails").show()