"""
processing/db_insertion.py
--------------------------
Loads scraped CSV data, cleans it, and upserts it into the MySQL star schema.

Usage:
    python processing/db_insertion.py --csv data/scraped_data.csv
"""

import ast
import argparse
import urllib.parse

import numpy as np
import pandas as pd
from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.dialects.mysql import insert


# ---------------------------------------------------------------------------
# Configuration  (override via environment variables in production)
# ---------------------------------------------------------------------------

import os

DB_USERNAME = os.getenv("DB_USERNAME", "jobs_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "change_me")
DB_HOST     = os.getenv("DB_HOST",     "127.0.0.1")
DB_PORT     = os.getenv("DB_PORT",     "3306")
DB_NAME     = os.getenv("DB_NAME",     "jobs")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_db_engine():
    pwd = urllib.parse.quote_plus(DB_PASSWORD)
    url = f"mysql+pymysql://{DB_USERNAME}:{pwd}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    return create_engine(url, echo=False)


def upsert(table, conn, keys, records):
    """Insert or update rows using MySQL's ON DUPLICATE KEY UPDATE."""
    if not records:
        return
    stmt = insert(table).values(records)
    update_cols = {c.key: c for c in stmt.inserted if c.key not in keys}
    conn.execute(stmt.on_duplicate_key_update(update_cols))


def clean_df(df: pd.DataFrame) -> pd.DataFrame:
    """Replace NaN with None and stringify object columns."""
    df = df.replace({np.nan: None})
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].apply(lambda x: str(x) if x is not None else None)
    return df


def parse_skills(value):
    """Safely parse a stringified list of skills back to a Python list."""
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            return ast.literal_eval(value)
        except (ValueError, SyntaxError):
            return [s.strip() for s in value.split(",") if s.strip()]
    return []


# ---------------------------------------------------------------------------
# Core insertion logic
# ---------------------------------------------------------------------------

def insert_data(df: pd.DataFrame) -> None:
    engine = get_db_engine()
    meta = MetaData()
    meta.reflect(bind=engine)

    with engine.begin() as conn:
        jobs_dim           = Table("jobs_dim",           meta, autoload_with=engine)
        companies_dim      = Table("companies_dim",      meta, autoload_with=engine)
        countries_dim      = Table("countries_dim",      meta, autoload_with=engine)
        cities_dim         = Table("cities_dim",         meta, autoload_with=engine)
        skills_dim         = Table("skills_dim",         meta, autoload_with=engine)
        job_postings_fact  = Table("job_postings_fact",  meta, autoload_with=engine)

        # --- dimension: jobs ---
        jobs_cols = ["job_title", "seniority_level", "employment_type"]
        upsert(jobs_dim, conn, jobs_cols,
               clean_df(df[jobs_cols].drop_duplicates()).to_dict("records"))

        # --- dimension: companies ---
        upsert(companies_dim, conn, ["company_name"],
               clean_df(df[["company_name"]].drop_duplicates()).to_dict("records"))

        # --- dimension: countries ---
        upsert(countries_dim, conn, ["country_name"],
               clean_df(df[["country_name"]].drop_duplicates()).to_dict("records"))

        # --- dimension: cities (needs country_id FK) ---
        country_id_map = pd.read_sql(
            "SELECT country_id, country_name FROM countries_dim", conn
        ).set_index("country_name")["country_id"].to_dict()

        cities_data = clean_df(df[["city_name", "country_name"]].drop_duplicates().copy())
        cities_data["country_id"] = cities_data["country_name"].map(country_id_map)
        upsert(cities_dim, conn, ["city_name", "country_id"],
               cities_data.to_dict("records"))

        # --- dimension: skills ---
        all_skills = {
            skill
            for skills_list in df["skills"]
            for skill in (skills_list if isinstance(skills_list, list) else [])
        }
        upsert(skills_dim, conn, ["skill_name"],
               clean_df(pd.DataFrame(list(all_skills), columns=["skill_name"])).to_dict("records"))

        # --- fetch ID maps ---
        jobs_id_map = pd.read_sql(
            "SELECT job_id, job_title, seniority_level, employment_type FROM jobs_dim", conn
        ).set_index(["job_title", "seniority_level", "employment_type"])["job_id"].to_dict()

        companies_id_map = pd.read_sql(
            "SELECT company_id, company_name FROM companies_dim", conn
        ).set_index("company_name")["company_id"].to_dict()

        cities_id_map = pd.read_sql(
            "SELECT city_id, city_name, country_id FROM cities_dim", conn
        ).set_index(["city_name", "country_id"])["city_id"].to_dict()

        skills_id_map = pd.read_sql(
            "SELECT skill_id, skill_name FROM skills_dim", conn
        ).set_index("skill_name")["skill_id"].to_dict()

        # --- fact: job_postings ---
        df = df.copy()
        df["job_id"]     = df.set_index(jobs_cols).index.map(jobs_id_map)
        df["company_id"] = df["company_name"].map(companies_id_map)
        df["country_id"] = df["country_name"].map(country_id_map)
        df["city_id"]    = df.set_index(["city_name", "country_id"]).index.map(cities_id_map)

        fact_cols = ["job_id", "company_id", "city_id", "posted_date"]
        upsert(job_postings_fact, conn, fact_cols,
               clean_df(df[fact_cols].drop_duplicates()).to_dict("records"))

        # --- bridge: job_posting_skills ---
        posting_ids = pd.read_sql(
            "SELECT posting_id, job_id, company_id, city_id, posted_date FROM job_postings_fact",
            conn,
        )
        df = df.merge(posting_ids, on=fact_cols)

        bridge = (
            df.explode("skills")[["posting_id", "skills"]]
            .copy()
            .rename(columns={"skills": "skill_name"})
        )
        bridge["skill_id"] = bridge["skill_name"].map(skills_id_map)
        bridge = clean_df(bridge[["posting_id", "skill_id"]].drop_duplicates())
        bridge.to_sql("job_posting_skills", conn, if_exists="append", index=False)

    print("✓ All data inserted successfully.")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Insert scraped job data into MySQL.")
    parser.add_argument("--csv", default="data/scraped_data.csv",
                        help="Path to the scraped CSV file.")
    args = parser.parse_args()

    df = pd.read_csv(args.csv)
    df["skills"] = df["skills"].apply(parse_skills)
    df = df.drop_duplicates()

    insert_data(df)
