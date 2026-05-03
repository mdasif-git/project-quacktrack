import streamlit as st
import pandas as pd
import numpy as np
import duckdb as ddb
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
DUCKDB_PATH = os.getenv("DUCKDB_PATH")

df = pd.DataFrame() #Empty DataFrame

# with ddb.connect(DUCKDB_PATH) as conn:
#     sql = """select
# distinct te.transaction_datetime,
# tr.bank,
# tr.category,
# tr.amount
# FROM transactions_refined AS tr
# left outer join 
# transactions_external AS te
# ON(tr.email_message_id = te.email_message_id)
# ;
#         """
#     df = conn.execute(sql).fetchdf()

st.set_page_config(page_title="Expense Dashboard", layout="wide")
st.title("📊 Expense Dashboard")
st.write(f"Welcome back, **{st.user.name}**!")

# --- 1. DATA FETCHING (Summary Metrics) ---
with ddb.connect(DUCKDB_PATH) as conn:
    # Query for Current Month Metrics (Debit vs Credit)
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    summary_sql = f"""
        SELECT 
            category,
            SUM(amount) as total
        FROM transactions_refined tr
        JOIN transactions_external te ON tr.email_message_id = te.email_message_id
        WHERE EXTRACT(MONTH FROM CAST(te.transaction_datetime AS DATE)) = {current_month}
          AND EXTRACT(YEAR FROM CAST(te.transaction_datetime AS DATE)) = {current_year}
        GROUP BY category
    """
    df_summary = conn.execute(summary_sql).fetchdf()

    # Query for Sub-type breakdown (Current Month Debits only)
    subtype_sql = f"""
        SELECT 
            sub_type,
            SUM(amount) as total
        FROM transactions_refined tr
        JOIN transactions_external te ON tr.email_message_id = te.email_message_id
        WHERE category = 'DEBIT'
          AND EXTRACT(MONTH FROM CAST(te.transaction_datetime AS DATE)) = {current_month}
          AND EXTRACT(YEAR FROM CAST(te.transaction_datetime AS DATE)) = {current_year}
        GROUP BY sub_type
    """
    df_subtypes = conn.execute(subtype_sql).fetchdf()

# --- 2. HEADER: CURRENT MONTH METRICS ---
st.subheader(f"Summary for {datetime.now().strftime('%B %Y')}")
# Top Row: Debit vs Credit
m1, m2 = st.columns(2)
debit_val = df_summary[df_summary['category'] == 'DEBIT']['total'].sum()
credit_val = df_summary[df_summary['category'] == 'CREDIT']['total'].sum()

m1.metric("Total Debit", f"₹{debit_val:,.2f}", delta_color="inverse")
m2.metric("Total Credit", f"₹{credit_val:,.2f}")

# Second Row: Sub-type Breakdown (Dynamic columns based on data)
if not df_subtypes.empty:
    st.write("**Debit Breakdown by Sub-type**")
    cols = st.columns(len(df_subtypes))
    for i, row in df_subtypes.iterrows():
        cols[i].metric(row['sub_type'], f"₹{row['total']:,.0f}")

st.divider()

# Placeholder for your Date-wise Expense Table
# st.subheader("Recipients without Categories")

# st.dataframe(df.head(10), width="stretch")


# --- 3. CHART: MONTH-OVER-MONTH COMPARISON ---
with ddb.connect(DUCKDB_PATH) as conn:
    chart_sql = """
        SELECT 
            DATE_TRUNC('month', CAST(te.transaction_datetime AS DATE)) AS month_date,
            tr.sub_type,
            SUM(tr.amount) AS amount_sum 
        FROM transactions_refined AS tr
        INNER JOIN transactions_external AS te ON tr.email_message_id = te.email_message_id
        WHERE tr.category = 'DEBIT'
          AND CAST(te.transaction_datetime AS DATE) >= (SELECT MAX(CAST(transaction_datetime AS DATE)) - INTERVAL 3 MONTH FROM transactions_external)
        GROUP BY 1, 2
        ORDER BY 1 ASC;
    """
    df_line = conn.execute(chart_sql).fetchdf()

st.subheader("Spend Trends: Last 3 Months (Summed)")

if not df_line.empty:
    # 1. Force convert to datetime64 so Streamlit treats it as a timeline, not strings
    df_line['month_date'] = pd.to_datetime(df_line['month_date'])

    # 2. Pivot the data
    # We want rows to be dates, columns to be sub-types
    df_pivot = df_line.pivot(index='month_date', columns='sub_type', values='amount_sum').fillna(0)

    # 3. Plot
    # Since the index is now datetime64, April will never come before January.
    st.line_chart(df_pivot)
else:
    st.info("No data found for the last 3 months.")

# with ddb.connect(DUCKDB_PATH) as conn:
#     sql = """
#         WITH BASE AS (select
#         distinct CAST(te.transaction_datetime AS date) AS transaction_date,
#         EXTRACT(MONTH FROM CAST(te.transaction_datetime AS date)) AS transaction_month,
#         EXTRACT(YEAR FROM CAST(te.transaction_datetime AS date)) AS transaction_year,
#         tr.bank,
#         tr.category,
#         tr.sub_type,
#         tr.amount
#         FROM transactions_refined AS tr
#         inner join 
#         transactions_external AS te
#         ON(tr.email_message_id = te.email_message_id)
#         WHERE category = 'DEBIT' and sub_type NOT IN('CREDIT CARD','BANK')
#         )

#         SELECT 
#         CONCAT(transaction_month,'-',transaction_year) AS month_year,
#         transaction_month,
#         transaction_year,
#         sub_type,
#         SUM(amount) AS amount_sum FROM 
#         base
#         GROUP BY ALL
#         order by 3 desc, 2 desc;
#     """
#     df_amounts = conn.execute(sql).fetchdf() 

# st.subheader("Debit Transactions")

# st.bar_chart(df_amounts.set_index('month_year')['amount_sum'])