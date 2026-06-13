"""
dags/job_scraper_dag.py
-----------------------
Airflow DAG that orchestrates the full jobs pipeline:
    scrape → process & store → notify

Schedule: daily at 06:00 UTC
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

# ---------------------------------------------------------------------------
# Paths  (set PROJECT_ROOT as an Airflow Variable or env var)
# ---------------------------------------------------------------------------

PROJECT_ROOT = os.getenv("PROJECT_ROOT", "/home/yosse/jobs-scraper")
DATA_DIR     = os.path.join(PROJECT_ROOT, "data")
CSV_PATH     = os.path.join(DATA_DIR, "scraped_data.csv")

# ---------------------------------------------------------------------------
# Default args
# ---------------------------------------------------------------------------

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2024, 6, 27),
    "email": ["hazemyossef0@gmail.com"],
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 3,
    "retry_delay": timedelta(minutes=2),
}

# ---------------------------------------------------------------------------
# DAG
# ---------------------------------------------------------------------------

with DAG(
    dag_id="job_scraper_pipeline",
    default_args=default_args,
    description="Scrape → process → store jobs data daily",
    schedule_interval="0 6 * * *",
    catchup=False,
    tags=["jobs", "scraping", "etl"],
) as dag:

    # ── Task 1: LinkedIn spider ──────────────────────────────────────────────
    scrape_linkedin = BashOperator(
        task_id="scrape_linkedin",
        bash_command=(
            f"cd {PROJECT_ROOT} && "
            f"scrapy crawl linkedin -o {CSV_PATH} -t csv"
        ),
    )

    # ── Task 2: Wuzzuf spider ────────────────────────────────────────────────
    scrape_wuzzuf = BashOperator(
        task_id="scrape_wuzzuf",
        bash_command=(
            f"cd {PROJECT_ROOT} && "
            f"scrapy crawl wuzzuf -o {CSV_PATH} -t csv"
        ),
    )

    # ── Task 3: Insert into MySQL ────────────────────────────────────────────
    def _insert_task(**_):
        """Load CSV and upsert into MySQL via db_insertion module."""
        import sys
        sys.path.insert(0, PROJECT_ROOT)

        import pandas as pd
        from processing.db_insertion import insert_data, parse_skills

        df = pd.read_csv(CSV_PATH)
        df["skills"] = df["skills"].apply(parse_skills)
        df = df.drop_duplicates()
        insert_data(df)

    insert_to_db = PythonOperator(
        task_id="insert_to_mysql",
        python_callable=_insert_task,
    )

    # ── Dependencies ─────────────────────────────────────────────────────────
    [scrape_linkedin, scrape_wuzzuf] >> insert_to_db
