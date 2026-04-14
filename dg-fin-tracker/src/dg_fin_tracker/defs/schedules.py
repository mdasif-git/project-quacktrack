import dagster as dg
from .assets import get_last_processed, fetch_emails, process_email, load_into_duckdb, bank_daily_partitions, bank_partitions, daily_partitions
from datetime import datetime, timedelta
# 1. Define the Job
# Dagster to runs all assets as a single unit.
email_pipeline_job = dg.define_asset_job(
    name="email_pipeline_job",
    selection=dg.AssetSelection.all()
)

@dg.schedule(
    job=email_pipeline_job, 
    cron_schedule="55 12,23 * * *", # 9:00 AM
    execution_timezone="Asia/Kolkata"
)
def email_daily_schedule(context: dg.ScheduleEvaluationContext):
    # 1. Get the 'Date' part of the current schedule tick
    # Dagster uses 'scheduled_execution_time' for the partition key
    # curr_date = context.scheduled_execution_time.strftime("%Y-%m-%d")
    

    previous_day = context.scheduled_execution_time.date() - timedelta(days=1)
    date = previous_day.strftime("%Y-%m-%d")

    return [
        dg.RunRequest(
            run_key=f"{bank}|{date}",
            partition_key=dg.MultiPartitionKey({"bank": bank, "date": date}),
        )
        for bank in bank_partitions.get_partition_keys()
    ]