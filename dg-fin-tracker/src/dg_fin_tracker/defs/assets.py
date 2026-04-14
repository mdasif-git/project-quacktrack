import dagster as dg
from dagster_duckdb import DuckDBResource
import os
from pathlib import Path
from dotenv import load_dotenv
import numpy as np
load_dotenv()
from dg_fin_tracker.configs.config import BANK_CONFIGS
from dg_fin_tracker.defs.resources import db_res
from dg_fin_tracker.defs.fetch_emails import *
from dg_fin_tracker.defs.process_emails import *
from dg_fin_tracker.defs.duckdb_load import *
import shutil
from datetime import datetime, timedelta
import json
import imaplib
import os
import email
import re
import pandas as pd
import time
from email.header import decode_header, make_header
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from datetime import datetime, timedelta
import spacy
from spacy.matcher import Matcher
import requests


# Load spacy model
nlp = spacy.load("en_core_web_sm",  disable=["parser"])
nlp.add_pipe("sentencizer")
matcher = Matcher(nlp.vocab)

# Gmail Configuration
GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")

# Data Paths
DATA_LANDING_PATH = Path(os.getenv("DATA_LANDING_PATH"))
DATA_INGESTION_PATH = Path(os.getenv("DATA_INGESTION_PATH"))
DATA_ARCHIVE_PATH = Path(os.getenv("DATA_ARCHIVE_PATH"))
DUCKDB_PATH = os.getenv("DUCKDB_PATH")
EXTERNAL_SCHEMA = os.getenv("EXTERNAL_SCHEMA")
PROMPTS_PATH = os.getenv("PROMPTS_PATH")

# Define the partitions
bank_partitions = dg.StaticPartitionsDefinition(["AXIS", "HDFC", "ICICI"])
daily_partitions = dg.DailyPartitionsDefinition(start_date="2026-03-23", timezone="Asia/Kolkata")

bank_daily_partitions = dg.MultiPartitionsDefinition(
    {
        "bank": bank_partitions,
        "date": daily_partitions,
    }
)

@dg.asset(partitions_def=bank_daily_partitions)
def get_last_processed(context: dg.AssetExecutionContext, duckdb: DuckDBResource):
    partition_keys = context.partition_key.keys_by_dimension
    bank_name = partition_keys["bank"]
    target_date = partition_keys["date"]

    context.log.info(f"Processing {bank_name} for date {target_date}")

    """Get the last processed transaction date for a bank."""
    with duckdb.get_connection() as conn:
        query = f"SELECT CAST(MAX(transaction_datetime) as date) as max_date FROM transactions_external WHERE bank='{bank_name}'"
        result = conn.execute(query).fetchone()

    if result and result[0]:
        return dg.Output(
            value=result[0],
            metadata={
                "last_date_found": str(result[0])
            }
        )
        
    else:
        return dg.Output(
            value="No data",
            metadata={
                "last_date_found": "No data"
            }
        )

@dg.asset(partitions_def=bank_daily_partitions)
def fetch_emails(context: dg.AssetExecutionContext,get_last_processed):
    partition_keys = context.partition_key.keys_by_dimension
    bank_name = partition_keys["bank"]
    target_date = partition_keys["date"]

    context.log.info(f"Processing {bank_name} for date {target_date}")

    last_date = get_last_processed
    
    # Filter your senders list by the current partition
    senders_map = {
        "AXIS": ["alerts@axisbank.com", "alerts@axis.bank.in"],
        "HDFC": ["alerts@hdfcbank.net", "alerts@hdfcbank.bank.in"],
        "ICICI": ["credit_cards@icicibank.com"]
    }


    emails = []
    for sender in senders_map[bank_name]:
        context.log.info(f"Last fetched date for {bank_name} is {last_date}")
        if(last_date is not None):
            context.log.info(f"Fetching emails for {bank_name} since {last_date}")
            files_path = get_emails(context,DATA_LANDING_PATH,last_date,{"id": sender, "bank": bank_name})

            if files_path and isinstance(files_path,str):
                emails.append(files_path)
    
    context.log.info(f"Retrieved {len(emails)} email files for bank {bank_name}")
    
    return dg.Output(
        value=emails,
        metadata={
            "bank": bank_name,
            "file_count": len(emails),
            "files": emails
        }
    )


@dg.asset(partitions_def=bank_daily_partitions)
def process_email(context: dg.AssetExecutionContext, fetch_emails: list):
    """Process emails from a specific bank partition."""
    partition_keys = context.partition_key.keys_by_dimension
    bank_name = partition_keys["bank"]
    target_date = partition_keys["date"]
    
    context.log.info(f"Processing {bank_name} for date {target_date}")

    all_processed_files = []

    
    context.log.info(f"Processing {len(fetch_emails)} files for bank: {bank_name}")
    
    for email_file in fetch_emails:
        context.log.info(f"Processing email file: {email_file}")
        processed_files = process_email_from_file(context, email_file, DATA_INGESTION_PATH, DATA_ARCHIVE_PATH, BANK_CONFIGS, nlp)
        
        # Handle both list and single file returns
        if isinstance(processed_files, list):
            all_processed_files.extend(processed_files)
        elif processed_files:
            all_processed_files.append(processed_files)
    
    context.log.info(f"Completed processing {len(all_processed_files)} files for bank: {bank_name}")
    
    return dg.Output(
        value=all_processed_files,
        metadata={
            "bank": bank_name,
            "files_processed": len(all_processed_files),
            "output_files": [str(f) for f in all_processed_files]
        }
    )

@dg.asset(partitions_def=bank_daily_partitions)
def load_into_duckdb(context: dg.AssetExecutionContext, process_email: list, duckdb: DuckDBResource):
    """Load processed emails for a specific bank partition into DuckDB."""
    
    partition_keys = context.partition_key.keys_by_dimension
    bank_name = partition_keys["bank"]
    target_date = partition_keys["date"]

    context.log.info(f"Loading {len(process_email)} files for bank {bank_name} for date {target_date} into DuckDB")
    
    for file in process_email:
        if file:
            context.log.info(f"Loading into DuckDB: {file}")
            load_into_external(context, file, duckdb, EXTERNAL_SCHEMA)
    
    return dg.Output(
        value=True,
        metadata={
            "bank": bank_name,
            "files_loaded": len(process_email)
        }
    )

@dg.asset(partitions_def=bank_daily_partitions)
def create_refined_table(context: dg.AssetExecutionContext, load_into_duckdb, duckdb: DuckDBResource):
    """Create refined table for a specific bank partition."""
    partition_keys = context.partition_key.keys_by_dimension
    bank_name = partition_keys["bank"]
    target_date = partition_keys["date"]

    context.log.info(f"Creating refined table")
    
    refined_table_name = "transactions_refined"
    create_refined(context, duckdb, EXTERNAL_SCHEMA, refined_table_name)
    
    return dg.Output(
        value=refined_table_name,
        metadata={
            "bank": None,
            "refined_table": refined_table_name
        }
    )   

@dg.asset(partitions_def=bank_daily_partitions)
def load_into_refined_regex_extractions(context: dg.AssetExecutionContext, create_refined_table: str, duckdb: DuckDBResource):
    """Load data from external to refined based on regex extractions for a specific bank partition."""
    partition_keys = context.partition_key.keys_by_dimension
    bank_name = partition_keys["bank"]
    target_date = partition_keys["date"]

    context.log.info(f"Loading refined data for bank {bank_name} for date {target_date} based on regex extractions")
    
    external_table_name = "transactions_external"
    refined_table_name = create_refined_table
    
    records_loaded = load_refined_from_regex(context, duckdb, external_table_name, refined_table_name, bank_name,target_date)
    
    return dg.Output(
        value=True,
        metadata={
            "bank": bank_name,
            "records_loaded": records_loaded
        }
    )

# @dg.asset(partitions_def=bank_daily_partitions)
# def load_into_refined_llm_extractions(context: dg.AssetExecutionContext, create_refined_table: str, duckdb: DuckDBResource):
#     """Load data from external to refined based on LLM extractions for a specific bank partition."""
#     partition_keys = context.partition_key.keys_by_dimension
#     bank_name = partition_keys["bank"]
#     target_date = partition_keys["date"]

#     context.log.info(f"Loading refined data for bank {bank_name} for date {target_date} based on LLM extractions")
    
#     external_table_name = "transactions_external"
#     refined_table_name = create_refined_table
#     with open(PROMPTS_PATH + "llm_extraction_prompt.txt", "r") as f:
#         llm_extraction_prompt = f.read()
#     records_loaded = load_refined_from_llm(context, duckdb, external_table_name, refined_table_name, bank_name,None, llm_extraction_prompt)
    
#     return dg.Output(
#         value=True,
#         metadata={
#             "bank": bank_name,
#             "records_loaded": records_loaded
#         }
#     )
@dg.asset(partitions_def=bank_daily_partitions)
def get_records_from_ingestion(context: dg.AssetExecutionContext, create_refined_table, duckdb: DuckDBResource):
    """Get records from ingestion table for a specific bank partition."""
    partition_keys = context.partition_key.keys_by_dimension
    bank_name = partition_keys["bank"]
    target_date = partition_keys["date"]

    context.log.info(f"Getting records from ingestion table for bank {bank_name} for date {target_date}")
    
    ingestion_table_name = "transactions_external"
    records = get_raw_records(context, duckdb, ingestion_table_name, bank_name,target_date)
    
    return dg.Output(
        value=records,
        metadata={
            "bank": bank_name,
            "record_count": len(records)
        }
    )

@dg.asset(partitions_def=bank_daily_partitions)
def llm_call_process_records(context: dg.AssetExecutionContext, get_records_from_ingestion, duckdb: DuckDBResource):
    """Local LLM Call for extraction of data for a specific bank partition."""
    partition_keys = context.partition_key.keys_by_dimension
    bank_name = partition_keys["bank"]
    target_date = partition_keys["date"]

    context.log.info(f"LLM Call for bank {bank_name} for date {target_date}")
    with open(PROMPTS_PATH + "llm_extraction_prompt.txt", "r") as f:
        llm_extraction_prompt = f.read()

    records = process_records_with_llm(context, get_records_from_ingestion, llm_extraction_prompt)
    
    return dg.Output(
        value=records,
        metadata={
            "bank": bank_name,
            "record_count": len(records)
        }
    )    
@dg.asset(partitions_def=bank_daily_partitions)
def load_into_refined_table(context: dg.AssetExecutionContext, llm_call_process_records, duckdb: DuckDBResource):
    """Load data from LLM processed records into refined table for a specific bank partition."""
    partition_keys = context.partition_key.keys_by_dimension
    bank_name = partition_keys["bank"]
    target_date = partition_keys["date"]

    context.log.info(f"Loading LLM processed records into refined table for bank {bank_name} for date {target_date}")

    refined_table_name = "transactions_refined"
    records_loaded = load_refined_table(context, duckdb, llm_call_process_records, refined_table_name)

    return dg.Output(
        value=True,
        metadata={
            "bank": bank_name,
            "records_loaded": records_loaded
        }
    )