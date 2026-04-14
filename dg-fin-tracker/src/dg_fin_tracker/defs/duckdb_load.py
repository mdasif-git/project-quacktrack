
import pandas as pd
import json
import numpy as np
import re
from datetime import datetime
import requests
# from config import (
#     DATA_LANDING_PATH,
#     DATA_INGESTION_PATH,
#     DATA_ARCHIVE_PATH,
#     DUCKDB_PATH,
#     EXTERNAL_SCHEMA,
#     logger
# )

# today_date = datetime.now().strftime("%Y-%m-%d")
# db_name = DUCKDB_PATH
# path = f"{DATA_INGESTION_PATH}/{today_date}"
# base_path = Path(path)

# def archive_files(source_dir, target_dir):
#     target_dir.mkdir(parents=True, exist_ok=True)
    
#     for item in base_path.iterdir():
#         # Build the full destination path
#         dest_path = target_dir / item.name
        
#         # Move the file or folder
#         shutil.move(str(item), str(dest_path))
#         print(f"Moved: {item.name}")   


def load_into_external(context,file_path,duckdb, EXTERNAL_SCHEMA):
    with duckdb.get_connection() as conn:
        with open(f"{EXTERNAL_SCHEMA}/ingestion_external.txt") as f:
            schema = f.read()

        # Create table if not exists
        context.log.info(f"Creating external table if not exists with schema: {schema}")
        conn.execute(f"CREATE TABLE IF NOT EXISTS transactions_external({schema})")

        # for csv_file in base_path.glob("*.csv"):
        # # Check if file has already been ingested
        # result = conn.execute(
        #     "SELECT COUNT(*) as count FROM transactions_external WHERE filename = ?",
        #     [csv_file.name]
        # ).fetchall()
        
        # if result[0][0] > 0:
        #     print(f"File {csv_file.name} already ingested. Skipping.")
        #     continue
        context.log.info(f"Checking for duplicates in file {file_path} before ingestion.")
        result = conn.execute("SELECT distinct email_message_id FROM read_csv(?, header=True) where email_message_id IN (SELECT distinct email_message_id FROM transactions_external)", [file_path.as_posix()]).fetchall()
        # if len(result[0][0]) > 0:
        if len(result) > 0:
            context.log.info(f"File {file_path} has duplicate email_message_id. Those messages will be skipped.")
            context.log.info(f"Duplicate email_message_id: {[row[0] for row in result]}")
        try:
            # Insert data using parameterized query
            conn.execute(
                """
                INSERT INTO transactions_external (email_message_id, email_From, Subject, email_Date, email_body_from_html, email_body_from_plain, bank, transaction_details_from_html, transaction_details_from_plain, transaction_type, transaction_detail_extracted_regex, filename, ingestion_date, llm_status)
                (SELECT email_message_id, email_From, Subject, email_Date, email_body_from_html, email_body_from_plain, bank, transaction_details_from_html, transaction_details_from_plain, transaction_type, transaction_detail_regex_extracted, ? AS filename, CURRENT_DATE() as ingestion_date, CAST(NULL AS STRING) as llm_status
                FROM read_csv(?, header=True) where email_message_id NOT IN (SELECT distinct email_message_id FROM transactions_external))
                """,
                [file_path.name, file_path.as_posix()]
            )
            context.log.info(conn.fetchall())
            context.log.info(f"Successfully ingested: {file_path}")
        except Exception as e:
            context.log.error(f"Failed to ingest {file_path}: {e}")



def create_refined(context,duckdb, EXTERNAL_SCHEMA, table_name):
    with duckdb.get_connection() as conn:
        with open(f"{EXTERNAL_SCHEMA}/refined_schema.txt") as f:
            schema = f.read()

        # Create table if not exists
        context.log.info(f"Creating refined table if not exists with schema: {schema}")
        conn.execute(f"CREATE TABLE IF NOT EXISTS {table_name}({schema})")


def load_refined_from_regex(context,duckdb, external_table_name, refined_table_name, bank_name, target_date=None):
    #Define iterations
    cnt = 0

    # Defining lists
    l__message_id = []
    l__bank = []
    l__email_body = []
    l__category = []
    l__sub_type = []
    l__amount = []
    l__info = []

    #Define dataframe
    df = pd.DataFrame()    
    
    # Define keys
    keys = ['BANK', 'CATEGORY', 'SUB_TYPE', 'AMOUNT', 'INFO']

    with duckdb.get_connection() as conn:
        context.log.info(f"Fetching records from {external_table_name}")

        sql_with_date = f"""select
                distinct 
                email_message_id,
                bank,
                transaction_details_from_plain,
                transaction_detail_extracted_regex
                from {external_table_name}
                where bank='{bank_name}' AND ingestion_date = '{target_date}' AND transaction_detail_extracted_regex is not null
                and transaction_detail_extracted_regex != 'pattern mismatch';"""
        sql_full_load = f"""select
                distinct 
                email_message_id,
                bank,
                transaction_details_from_plain,
                transaction_detail_extracted_regex
                from {external_table_name}
                where bank='{bank_name}' AND transaction_detail_extracted_regex is not null
                and transaction_detail_extracted_regex != 'pattern mismatch' AND email_message_id NOT IN (SELECT DISTINCT email_message_id FROM transactions_refined WHERE bank = '{bank_name}');"""        
        
        if(target_date is not None):
            sql = sql_with_date
        else:
            sql = sql_full_load

        context.log.info(f"Executing SQL: {sql}")
        records = conn.execute(sql).fetchall()
        context.log.info(f"Fetched {len(records)} records")
        if(len(records) == 0):
            context.log.info(f"No records to process for bank {bank_name} and date {target_date}")
            return 0
        else:
            context.log.info(f"Processing {len(records)} records for bank {bank_name} and date {target_date}")

            def quote_naked(match):
                val = match.group(1).strip()
                # Remove the backslash if it exists
                val = val.replace('\\', '')
                return f'"{key}": "{val}"'

            for record in records:
                context.log.info(f"Number of iteration: {cnt}")
                remaining = len(records) - cnt - 1
                context.log.info(f"Iteration left: {remaining}")
                
                # Regex Extraction
                regex_str = record[3]
                # 1. First, convert ONLY the keys to double quotes. 
                # We look for 'Key': at the start or after a space/comma.
                s = re.sub(r"'(\w+)':", r'"\1":', regex_str)  # Fix keys
                s = re.sub(r":\s*'([^']*)'", r': \1', s) # Remove quotes from values
                # 2. Define our keys for the lookahead boundary
                
                lookahead = r'(?=\s*,\s*"(?:' + '|'.join(keys) + r')":|\s*})'
                
                for key in keys:
                    # This pattern only matches if the value DOES NOT start with ' or "
                    # (?!["\']) is the guard rail you asked for.
                    pattern = rf'"{key}":\s*(?!["\'])(.*?){lookahead}'
                    s = re.sub(pattern, quote_naked, s)
                regex_dict = json.loads(s)

                #Load list values
                l__message_id.append(record[0])
                l__bank.append(record[1])
                l__email_body.append(record[2])
                l__category.append(regex_dict['CATEGORY'])
                l__sub_type.append(regex_dict['SUB_TYPE'])
                if( not(isinstance(regex_dict['AMOUNT'], float))):
                    regex_dict['AMOUNT'] = float((regex_dict['AMOUNT']).replace(',',''))
                l__amount.append(regex_dict['AMOUNT'])
                l__info.append(regex_dict['INFO'])

                cnt+=1

            df['message_id'] = l__message_id
            df['bank'] = l__bank
            df['email'] = l__email_body
            df['category'] = l__category
            df['sub_type'] = l__sub_type
            df['amount'] = l__amount
            df['info'] = l__info 


            # Insert data into refined
            try:
                conn.execute(
                    f"""
                    INSERT INTO {refined_table_name} (email_message_id, bank, email_body, category, sub_type, amount, info, extracted_via, load_date)
                    (SELECT message_id, bank, email, category, sub_type, amount, info, ? AS extracted_via, ? AS load_date 
                    FROM df)
                    """,
                    ["regex", datetime.now().strftime("%Y-%m-%d")]
                )
                context.log.info(conn.fetchall())
                context.log.info(f"Successfully loaded refined data")
                return len(df)
            except Exception as e:
                context.log.error(f"Failed to load refined data: {e}")
                return e


def load_refined_from_llm(context,duckdb, external_table_name, refined_table_name, bank_name, target_date=None, prompt=None):
    #Define iterations
    cnt = 0

    # Defining lists
    l__message_id = []
    l__bank = []
    l__email_body = []
    l__category = []
    l__sub_type = []
    l__amount = []
    l__info = []
    l__input_tokens = []
    l__output_tokens = []
    l__tokens_per_second = []

    #Define dataframe
    df = pd.DataFrame()    


    def proces_trn_dtl(input_text, prompt): 
        payload = {
            "model": "gemma-4-e4b-it",
            "temperature": 0,
            "system_prompt": prompt,
        "input":input_text}
        Headers = {"Content-Type": "application/json"}
        url = "http://localhost:1234/api/v1/chat"
        
        response = requests.post(url, json=payload, headers=Headers)
        model_response = response.text
        model_response_formatted = json.loads(model_response)
        print(model_response_formatted)
        return model_response_formatted

    with duckdb.get_connection() as conn:
        context.log.info(f"Fetching records from {external_table_name}")

        sql_with_date = f"""select
                distinct 
                email_message_id,
                bank,
                transaction_details_from_plain,
                transaction_detail_extracted_regex
                from {external_table_name}
                where bank='{bank_name}' AND ingestion_date = '{target_date}' AND (transaction_detail_extracted_regex is null
                or transaction_detail_extracted_regex = 'pattern mismatch') AND email_message_id NOT IN (SELECT DISTINCT email_message_id FROM transactions_refined WHERE bank = '{bank_name}');"""
        sql_full_load = f"""select
                distinct 
                email_message_id,
                bank,
                transaction_details_from_plain,
                transaction_detail_extracted_regex
                from {external_table_name}
                where bank='{bank_name}' AND (transaction_detail_extracted_regex is null
                or transaction_detail_extracted_regex = 'pattern mismatch') AND email_message_id NOT IN (SELECT DISTINCT email_message_id FROM transactions_refined WHERE bank = '{bank_name}');"""        
        
        if(target_date is not None):
            sql = sql_with_date
        else:
            sql = sql_full_load

        context.log.info(f"Executing SQL: {sql}")
        records = conn.execute(sql).fetchall()

    context.log.info(f"Fetched {len(records)} records")
    if(len(records) == 0):
        context.log.info(f"No records to process for bank {bank_name} and date {target_date}")
        return 0
    else:
        context.log.info(f"Processing {len(records)} records for bank {bank_name} and date {target_date}")


    for record in records:
        context.log.info(f"Number of iteration: {cnt}")
        remaining = len(records) - cnt - 1
        context.log.info(f"Iteration left: {remaining}")
    
        # LLM Call
        model_response = proces_trn_dtl(record[2],prompt)
        output = json.loads(model_response['output'][0]['content'])

        if("STATUS" in output.keys() and "IGNORED" in output.values()):
            category = None
            sub_type = None
            amount = None
            info = None
        else:
            category = output['CATEGORY']
            sub_type = output['SUB_TYPE']
            amount = output['AMOUNT']
            info = output['INFO']

        
        # Stats
        ip_tokens = model_response['stats']['input_tokens']
        op_tokens = model_response['stats']['total_output_tokens']
        tps = model_response['stats']['tokens_per_second']
        
        l__message_id.append(record[0])
        l__bank.append(record[1])
        l__email_body.append(record[2])
        l__category.append(category)
        l__sub_type.append(sub_type)
        l__amount.append(amount)
        l__info.append(info)
        l__input_tokens.append(ip_tokens)
        l__output_tokens.append(op_tokens)
        l__tokens_per_second.append(tps)
        
        cnt+=1

    df['message_id'] = l__message_id
    df['bank'] = l__bank
    df['email'] = l__email_body
    df['category'] = l__category
    df['sub_type'] = l__sub_type
    df['amount'] = l__amount
    df['info'] = l__info 
    df['input_tokens'] = l__input_tokens
    df['output_tokens'] = l__output_tokens
    df['tokens_per_second'] = l__tokens_per_second

    # Insert data into refined
    with duckdb.get_connection() as conn:
        context.log.info(f"Inserting LLM extracted data into {refined_table_name} for bank {bank_name} and date {target_date}")
        try:
            conn.execute(
                f"""
                INSERT INTO {refined_table_name} (email_message_id, bank, email_body, category, sub_type, amount, info, extracted_via, load_date)
                (SELECT message_id, bank, email, category, sub_type, amount, info, ? AS extracted_via, ? AS load_date 
                FROM df)
                """,
                ["llm", datetime.now().strftime("%Y-%m-%d")]
            )
            context.log.info(conn.fetchall())
            context.log.info(f"Successfully loaded refined data")
            return len(df)
        except Exception as e:
            context.log.error(f"Failed to load refined data: {e}")
            return e


def get_raw_records(context, duckdb, external_table_name, bank_name, target_date=None):
    query_filter = f"ingestion_date = '{target_date}'" if target_date else "1=1"
    
    sql = f"""
        SELECT DISTINCT 
            email_message_id, 
            bank, 
            transaction_details_from_plain,
            transaction_detail_extracted_regex
        FROM {external_table_name}
        WHERE bank='{bank_name}' 
        AND ({query_filter})
        AND (transaction_detail_extracted_regex IS NULL OR transaction_detail_extracted_regex = 'pattern mismatch') AND email_message_id NOT IN (SELECT DISTINCT email_message_id FROM transactions_refined WHERE bank = '{bank_name}');
    """
    
    with duckdb.get_connection() as conn:
        context.log.info(f"Fetching records from {external_table_name}")
        context.log.info(f"Executing SQL: {sql}")
        df_raw = conn.execute(sql).df() # DuckDB can return a df directly
    
    return df_raw


def process_records_with_llm(context, df_raw, prompt):
    def proces_trn_dtl(input_text, prompt): 
        payload = {
            "model": "gemma-4-e4b-it",
            "temperature": 0,
            "system_prompt": prompt,
            "input": input_text
        }
        response = requests.post("http://localhost:1234/api/v1/chat", json=payload)
        return response.json()

    results = []
    total_records = len(df_raw)

    for i, row in df_raw.iterrows():
        try:
            context.log.info(f"Processing record {i+1}/{total_records}")
            
            model_res = proces_trn_dtl(row['transaction_details_from_plain'], prompt)
            # Use .get() with defaults to avoid KeyErrors
            output_content = model_res.get('output', [{}])[0].get('content', '{}')
            output = json.loads(output_content)

            # Data extraction logic
            #TODO: PyDantic evalutation of output to check if it is valid or if it has the "IGNORED" status
            is_ignored = "STATUS" in output and output["STATUS"] == "IGNORED"


            # Use .get(key, None) so missing values become None (JSON null) instead of NaN
            stats = model_res.get('stats', {})
            context.log.info(f"LLM output for record {i+1}: {output}")
            context.log.info(f"LLM stats for record {i+1}: {stats}")

            results.append({
                'message_id': row['email_message_id'],
                'bank': row['bank'],
                'email': row['transaction_details_from_plain'],
                'category': None if is_ignored else output.get('CATEGORY'),
                'sub_type': None if is_ignored else output.get('SUB_TYPE'),
                'amount': None if is_ignored else output.get('AMOUNT'),
                'info': None if is_ignored else output.get('INFO'),
                # Convert potential NaNs to 0 or None
                'input_tokens': stats.get('input_tokens', 0),
                'output_tokens': stats.get('total_output_tokens', 0),
                'tokens_per_second': stats.get('tokens_per_second', 0)
            })
        except Exception as e:
            context.log.error(f"Error processing record {i}: {e}")
            continue

    final_df = pd.DataFrame(results).replace({np.nan: None})
    return final_df

def load_refined_table(context, duckdb, df_refined, refined_table_name):
    if df_refined.empty:
        context.log.info("No records to insert.")
        return 0

    with duckdb.get_connection() as conn:
        try:
            load_date = datetime.now().strftime("%Y-%m-%d")
            conn.execute(
                f"""
                INSERT INTO {refined_table_name} 
                (email_message_id, bank, email_body, category, sub_type, amount, info, extracted_via, load_date, audit_input_tokens, audit_output_tokens, audit_tokens_per_second)
                SELECT message_id, bank, email, category, sub_type, amount, info, 'llm', '{load_date}', input_tokens, output_tokens, tokens_per_second
                FROM df_refined
                """
            )
            context.log.info(f"Successfully loaded {len(df_refined)} records into {refined_table_name}")
            return len(df_refined)
        except Exception as e:
            context.log.error(f"Failed to load refined data: {e}")
            raise e
# archive_files(base_path, archive_path)
