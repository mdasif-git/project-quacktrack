import duckdb
from pathlib import Path
import os
import pandas as pd
from dotenv import load_dotenv
import shutil
from datetime import datetime, timedelta
load_dotenv()

from config import (
    DATA_LANDING_PATH,
    DATA_INGESTION_PATH,
    DATA_ARCHIVE_PATH,
    DUCKDB_PATH,
    EXTERNAL_SCHEMA,
    logger
)

today_date = datetime.now().strftime("%Y-%m-%d")
db_name = DUCKDB_PATH
path = f"{DATA_INGESTION_PATH}/2026-02-26"
base_path = Path(path)

# def archive_files(source_dir, target_dir):
#     target_dir.mkdir(parents=True, exist_ok=True)
    
#     for item in base_path.iterdir():
#         # Build the full destination path
#         dest_path = target_dir / item.name
        
#         # Move the file or folder
#         shutil.move(str(item), str(dest_path))
#         print(f"Moved: {item.name}")   


with open(f"{EXTERNAL_SCHEMA}/ingestion_external.txt") as f:
    schema = f.read()


with duckdb.connect(db_name) as conn:
    # Create table if not exists
    conn.execute(f"CREATE TABLE IF NOT EXISTS transactions_external({schema})")

    for csv_file in base_path.glob("*.csv"):
        # # Check if file has already been ingested
        # result = conn.execute(
        #     "SELECT COUNT(*) as count FROM transactions_external WHERE filename = ?",
        #     [csv_file.name]
        # ).fetchall()
        
        # if result[0][0] > 0:
        #     print(f"File {csv_file.name} already ingested. Skipping.")
        #     continue
    
        result = conn.execute("SELECT distinct email_message_id FROM read_csv(?, header=True) where email_message_id IN (SELECT distinct email_message_id FROM transactions_external)", [csv_file.as_posix()]).fetchall()
        # if len(result[0][0]) > 0:
        if len(result) > 0:
            logger.info(result[0][0])
            logger.info(f"File {csv_file.name} has duplicate email_message_id. Those messages will be skipped.")
            logger.info(f"Duplicate email_message_id: {[row[0] for row in result]}")
        try:
            # Insert data using parameterized query
            conn.execute(
                """
                INSERT INTO transactions_external 
                (SELECT *, ? AS filename, CURRENT_DATE() as ingestion_date, CAST(NULL AS STRING) as llm_status
                FROM read_csv(?, header=True) where email_message_id NOT IN (SELECT distinct email_message_id FROM transactions_external))
                """,
                [csv_file.name, csv_file.as_posix()]
            )
            logger.info(conn.fetchall())
            logger.info(f"Successfully ingested: {csv_file.name}")
        except Exception as e:
            logger.error(f"Failed to ingest {csv_file.name}: {e}")

# archive_files(base_path, archive_path)
