# ingest_loseit_and_glucose.py
# Updated to only handle Lose It data ingestion

import os
import zipfile
import pandas as pd
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'host': os.getenv("PGHOST", "localhost"),
    'dbname': os.getenv("PGDB", "health_data"),
    'user': os.getenv("PGUSER", os.getlogin()),
    'password': os.getenv("PGPASS", ""),
    'port': os.getenv("PGPORT", "5432")
}

LOSEIT_ZIP_PATH = os.getenv("LOSEIT_ZIP_PATH")

def get_db_connection():
    try:
        return psycopg2.connect(**DB_CONFIG)
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return None

def normalize_col(col):
    return col.lower().strip().replace(" ", "_").replace("(", "").replace(")", "").replace("/", "_").replace("-", "_").replace("%", "percent")

def insert_df(df, table, cols):
    if df.empty:
        return 0
    df.columns = [normalize_col(c) for c in df.columns]
    missing = [c for c in cols if c not in df.columns]
    if missing:
        print(f"⚠️ Skipping {table}: missing columns {missing}")
        return 0

    df = df[cols]
    # Convert 'calories_consumed' to numeric, handling commas
    if 'calories_consumed' in df.columns:
        df['calories_consumed'] = df['calories_consumed'].astype(str).str.replace(',', '', regex=False)
        df['calories_consumed'] = pd.to_numeric(df['calories_consumed'], errors='coerce')
    conn = get_db_connection()
    cur = conn.cursor()
    rows = [tuple(row) for row in df.to_numpy()]
    
    col_str = ', '.join(cols)
    placeholders = ', '.join(['%s'] * len(cols))
    query = f"INSERT INTO {table} ({col_str}) VALUES ({placeholders}) ON CONFLICT DO NOTHING;"
    
    try:
        cur.executemany(query, rows)
        conn.commit()
        return cur.rowcount
    except Exception as e:
        print(f"❌ Insert failed for {table}: {e}")
        conn.rollback()
        return 0
    finally:
        cur.close()
        conn.close()

def ingest_loseit_zip(zip_path):
    with zipfile.ZipFile(zip_path, 'r') as z:
        def load_csv(name):
            try:
                with z.open(name) as f:
                    df = pd.read_csv(f)
                    df.columns = [normalize_col(c) for c in df.columns]
                    return df
            except Exception as e:
                print(f"⚠️ Could not load {name}: {e}")
                return pd.DataFrame()

        food_df = load_csv('food-logs.csv')

        # Rename columns to match DB schema
        food_df = food_df.rename(columns={
            'date': 'log_date',
            'name': 'food_item',
            'meal': 'meal_type',
            'calories': 'calories_consumed',
            'carbohydrates_g': 'carbs_g',
            'sugars_g': 'sugar_g'
        })

        inserts = {}
        inserts['food_log'] = insert_df(
            food_df,
            'food_log',
            ['log_date', 'food_item', 'meal_type', 'calories_consumed', 'fat_g', 'protein_g', 'carbs_g', 'sugar_g', 'fiber_g', 'sodium_mg']
        )

        print("\nIngestion Summary from Lose It ZIP:")
        for table, count in inserts.items():
            print(f"{table:<20}: {count} rows inserted")

def main():
    ingest_loseit_zip(LOSEIT_ZIP_PATH)

if __name__ == '__main__':
    main()
