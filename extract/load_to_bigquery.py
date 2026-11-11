import os
from pathlib import Path
import pandas as pd
from datetime import datetime, timezone
from google.cloud import bigquery
from google.oauth2 import service_account

from extract.extract_accommodation import df_accomod

BASE_DIR = Path(__file__).resolve().parent.parent

KEY_PATH = BASE_DIR / "gcp-key.json"
credentials = service_account.Credentials.from_service_account_file(KEY_PATH)
client = bigquery.Client(credentials=credentials, project=credentials.project_id)

PROJECT_ID = client.project
DATASET_ID = "raw"
LOCATION = "EU"

dataset_ref = bigquery.DatasetReference(PROJECT_ID, DATASET_ID)
dataset = bigquery.Dataset(dataset_ref)
dataset.location = LOCATION

dataset = client.create_dataset(dataset, exists_ok=True)

def upload_df_to_bigquery(df:pd.DataFrame, table_name: str):
    df["_loaded_at"] = datetime.now(timezone.utc)

    table_ref = f"{PROJECT_ID}.{DATASET_ID}.{table_name}"

    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        autodetect=True
    )
    job = client.load_table_from_dataframe(df, table_ref, job_config=job_config)
    job.result()
    table = client.get_table(table_ref)

prices_path = BASE_DIR / "data"/ "raw"/ "numbeo_prices.csv"
if prices_path.exists():
    df_prices = pd.read_csv(prices_path)
    upload_df_to_bigquery(df_prices,"numbeo_prices")
else:
    print(f"File not found: {prices_path}")
accomod_path = BASE_DIR/ "data"/ "raw"/ "accommodation_raw.csv"
if accomod_path.exists():
    df_accomod = pd.read_csv(accomod_path)
    upload_df_to_bigquery(df_accomod, "accommodation")
else:
    print(f"File not found: {accomod_path}")
