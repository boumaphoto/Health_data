# config.py
from pathlib import Path
import os, getpass
from dotenv import load_dotenv

load_dotenv()                          # reads values from .env
PROJECT_DIR = Path(__file__).parent

DB = dict(
    host = os.getenv("PGHOST", "localhost"),
    dbname = os.getenv("PGDB", "health_data"),
    user = os.getenv("PGUSER", getpass.getuser()),
    password = os.getenv("PGPASS", ""),
)

BATCH = int(os.getenv("BATCH", "10000"))   # rows per bulk insert
TZ    = os.getenv("TZ", "UTC")             # fallback time-zone

import pandas as pd, psycopg2, sys, pathlib
DB = dict(host="localhost", dbname="health_data",
          user="your_user", password="your_pwd")

csv_path = pathlib.Path("/path/to/weight_gurus_export.csv")   # <-- edit

COL_MAP = {                # tweak to match actual headers
    "Date":        "measurement_date",
    "Weight":      "weight_value",
    "Unit":        "weight_unit",
    "Body Fat %":  "body_fat_percentage",
    "BMI":         "bmi_value",
    "Muscle lb":   "muscle_mass",
}

def load_csv(p):
    df = pd.read_csv(p)
    df = df.rename(columns=COL_MAP)
    df["measurement_date"] = pd.to_datetime(df["measurement_date"],
                                            errors="coerce", utc=True)
    num_cols = ["weight_value","body_fat_percentage","bmi_value","muscle_mass"]
    df[num_cols] = df[num_cols].apply(pd.to_numeric, errors="coerce")
    df = df.dropna(subset=["measurement_date","weight_value"])
    df["source"] = "WeightGurus"
    return df[["measurement_date","weight_value","weight_unit",
               "body_fat_percentage","bmi_value","muscle_mass","source"]]

def main():
    df = load_csv(csv_path)
    if df.empty:
        print("Nothing to insert.")
        return
    with psycopg2.connect(**DB) as conn, conn.cursor() as cur:
        cur.executemany("""
            INSERT INTO body_measurements
              (measurement_date,weight_value,weight_unit,
               body_fat_percentage,bmi_value,muscle_mass,source)
            VALUES (%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (measurement_date,source) DO NOTHING;
        """, df.astype(object).where(pd.notna(df), None).values.tolist())
        print(f"Inserted {cur.rowcount} rows.")

if __name__ == "__main__":
    main()
