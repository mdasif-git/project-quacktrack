import streamlit as st
import pandas as pd
import numpy as np
import duckdb as ddb
import os
from dotenv import load_dotenv


load_dotenv()
DUCKDB_PATH = os.getenv("DUCKDB_PATH")

df = pd.DataFrame() #Empty DataFrame
# Global Filter
st.divider()
st.subheader("📊 Chart Controls")
exclude_bulk = st.checkbox("Exclude Initial Bulk Load (>100k input tokens)", value=False)

with ddb.connect(DUCKDB_PATH) as conn:
    sql = """
    SELECT 
        load_date,
        COUNT(CASE WHEN extracted_via = 'llm' THEN 1 END) as llm_count,
        COUNT(CASE WHEN extracted_via = 'regex' THEN 1 END) as regex_count,
        SUM(audit_input_tokens) as total_input,
        SUM(audit_output_tokens) as total_output,
        AVG(audit_tokens_per_second) as avg_speed
    FROM transactions_refined
    GROUP BY load_date
    ORDER BY load_date ASC;
    """
    df = conn.execute(sql).fetchdf()
if exclude_bulk:
    # Filter out the massive load from April 14th
    df_filtered = df[((df['total_input'] < 100000) | (df['total_input'].isna())) & ((df['regex_count'] <= 1000))].copy()
    st.caption("⚠️ Currently hiding bulk load days to show daily trends.")
else:
    df_filtered = df.copy()

# Ensure numeric types and dates
df_filtered['load_date'] = pd.to_datetime(df_filtered['load_date']).astype('datetime64[ns]')
df_filtered[['llm_count', 'regex_count']] = df_filtered[['llm_count', 'regex_count']].fillna(0).astype(int)

# 2. Key Performance Indicators (KPIs)
total_tokens = df_filtered['total_input'].sum() + df_filtered['total_output'].sum()
avg_efficiency = df_filtered['avg_speed'].mean()


col1, col2, col3 = st.columns(3)
col1.metric("Lifetime Tokens", f"{total_tokens:,}")
col2.metric("Avg Speed", f"{avg_efficiency:.2f} t/s")
last_date_str = df_filtered['load_date'].max().strftime('%Y-%m-%d')
col3.metric("Last Load Date", last_date_str)
# col3.metric("Last Load Date", df['load_date'].dt.date.max())


st.divider()

st.title("🤖 LLM Audit Dashboard")

# 3. Token Consumption Time Series (Input vs Output)
st.subheader("Token Usage Trend")
# We set the index to load_date so the chart uses it as the X-axis
token_chart_data = df_filtered.set_index('load_date')[['total_input', 'total_output']]

st.bar_chart(df_filtered.set_index('load_date')[['total_input', 'total_output']])
# st.bar_chart(token_chart_data) # Optional: Add a bar chart for clearer comparison

# 4. Performance Metric (Tokens per Second)
st.subheader("Model Latency (Tokens/Sec)")
speed_chart_data = df_filtered.set_index('load_date')['avg_speed']

st.line_chart(speed_chart_data, color="#FFaa00") # Custom yellow-ish color for QuackTrack

# 5. Raw Audit Logs (Optional)
with st.expander("View Raw Audit Data"):
    st.dataframe(df_filtered, use_container_width=True)


st.divider()
st.subheader("🤖 Extraction Strategy: LLM vs Regex")

# Calculate Global Percentages
total_llm = df_filtered['llm_count'].sum()
total_regex = df_filtered['regex_count'].sum()
total_overall = total_llm + total_regex

if total_overall > 0:
    llm_pct = (total_llm / total_overall) * 100
    regex_pct = (total_regex / total_overall) * 100

    # Display as a "Usage Progress Bar"
    st.write(f"Overall LLM Adoption: **{llm_pct:.1f}%**")
    st.progress(llm_pct / 100)
else:
    st.info("No extraction data found.")

# 3. Create a Bar Chart for daily strategy
# This shows if certain days relied more on Regex than others
strategy_data = df_filtered.set_index('load_date')[['llm_count', 'regex_count']]
st.bar_chart(strategy_data)

