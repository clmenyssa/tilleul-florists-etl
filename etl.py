"""Tilleul florists ETL.

Extract:   the florists of the Rhône from the API Recherche d'entreprises
           -> the raw answer is saved in the data lake (Amazon S3)
Transform: read the raw file back, keep the real prospects
Load:      write today's snapshot in the warehouse (Amazon RDS for PostgreSQL)
"""
import json
import logging
import os
import time
from datetime import date

import boto3
import requests
from dotenv import load_dotenv
from sqlalchemy import URL, create_engine, text

from cleaning import clean_florists

load_dotenv()
logging.basicConfig(level=logging.WARNING, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("tilleul-etl")
log.setLevel(logging.INFO)

API_URL = "https://recherche-entreprises.api.gouv.fr/search"
BUCKET = os.environ["S3_BUCKET"]
TODAY = date.today()


def get_json(params):
    """One GET request; wait and try again on 429 (rate limit)."""
    for attempt in range(5):
        response = requests.get(API_URL, params=params, timeout=30)
        if response.status_code == 429:
            time.sleep(2 ** attempt)
            continue
        response.raise_for_status()
        return response.json()
    raise RuntimeError("Still rate limited after 5 attempts")


def extract():
    """Collect every page of florists, save the raw answer in S3, return its key."""
    params = {
        "activite_principale": "47.76Z",
        "departement": "69",
        "etat_administratif": "A",
        "minimal": "true",
        "include": "siege",
        "per_page": 25,
        "page": 1,
    }
    first_page = get_json(params)
    companies = first_page["results"]
    for page in range(2, first_page["total_pages"] + 1):
        params["page"] = page
        companies.extend(get_json(params)["results"])
        time.sleep(0.2)
    log.info("Extract: %s florists collected (%s announced)", len(companies), first_page["total_results"])

    key = f"raw/florists/{TODAY}.json"
    body = json.dumps(companies, ensure_ascii=False).encode("utf-8")
    s3 = boto3.client("s3")
    s3.put_object(Bucket=BUCKET, Key=key, Body=body, ContentType="application/json")
    log.info("Extract: raw file saved in S3 as %s (%s KB)", key, len(body) // 1024)
    return key


def transform(key):
    """Read the raw file from S3 and keep the florists that Tilleul may contact."""
    s3 = boto3.client("s3")
    raw = s3.get_object(Bucket=BUCKET, Key=key)["Body"].read()
    companies = json.loads(raw)
    prospects = clean_florists(companies)
    prospects.insert(0, "snapshot_date", TODAY)
    log.info("Transform: %s prospects kept out of %s companies", len(prospects), len(companies))
    return prospects


def get_engine():
    url = URL.create(
        "postgresql+psycopg",
        username=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        host=os.environ["DB_HOST"],
        port=int(os.environ["DB_PORT"]),
        database=os.environ["DB_NAME"],
    )
    return create_engine(url, connect_args={"sslmode": "require"})


def load(prospects):
    """Replace today's snapshot in the warehouse: running twice gives the same result."""
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS florist_snapshots (
                snapshot_date    DATE NOT NULL,
                siren            TEXT NOT NULL,
                name             TEXT,
                head_office_city TEXT,
                headcount_band   TEXT,
                open_shops       INTEGER,
                PRIMARY KEY (snapshot_date, siren)
            )
        """))
        deleted = conn.execute(
            text("DELETE FROM florist_snapshots WHERE snapshot_date = :day"), {"day": TODAY}
        ).rowcount
        prospects.to_sql("florist_snapshots", conn, if_exists="append", index=False)
    log.info("Load: %s rows written for %s (%s old rows replaced)", len(prospects), TODAY, deleted)


def main():
    key = extract()
    prospects = transform(key)
    load(prospects)
    log.info("Done")


if __name__ == "__main__":
    main()
