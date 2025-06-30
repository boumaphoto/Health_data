# ingest_loseit_and_glucose.py
import os
import zipfile
import argparse
import pandas as pd
import psycopg2
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

DB_CONFIG = {
    'host': os.getenv("PGHOST", "localhost"),
    'dbname': os.getenv("PGDB", "health_data"),
    'user': os.getenv("PGUSER", os.getlogin()),
    'password': os.getenv("PGPASS", ""),
    'port': os.getenv("PGPORT", "5432")
}

LOSEIT_ZIP_PATH = os.getenv("LOSEIT_ZIP_PATH")
BLOODSUGAR_CSV_PATH = os.getenv("BLOODSUGAR_CSV_PATH")

def get_db_connection():
    try:
        return psycopg2.connect(**DB_CONFIG)
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return None

def normalize_col(col):
    return col.lower().strip().replace(" ", "_").replace("(", "").replace(")", "").replace("/", "_").replace("-", "_").replace("%", "percent")

def parse_date(date_str):
    for fmt in ("%m/%d/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(date_str, fmt).date()
        except:
            continue
    return None

def insert_df(df, table, cols, transform_func=None):
    if df.empty:
        return 0
    df.columns = [normalize_col(c) for c in df.columns]
    missing = [c for c in cols if c not in df.columns]
    if missing:
        print(f"⚠️ Skipping {table}: missing columns {missing}")
        return 0

    df = df[cols]
    if transform_func:
        df = df.apply(transform_func, axis=1)

    conn = get_db_connection()
    cur = conn.cursor()
    rows = [tuple(row) for row in df.to_numpy()]

    col_str = ', '.join(cols)
    placeholders = ', '.join(['%s'] * len(cols))
    # Corrected ON CONFLICT to use a unique constraint from the table
    query = f"INSERT INTO {table} ({col_str}) VALUES ({placeholders}) ON CONFLICT (log_date, name, meal) DO NOTHING;"
    if table == 'blood_glucose':
        query = f"INSERT INTO {table} ({col_str}) VALUES ({placeholders}) ON CONFLICT (reading_time, glucose_value) DO NOTHING;"


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

def ingest_loseit_zip(zip_path, start=None, end=None):
    with zipfile.ZipFile(zip_path, 'r') as z:
        def load_csv(name):
            try:
                with z.open(name) as f:
                    df = pd.read_csv(f)
                    df.columns = [normalize_col(c) for c in df.columns]
                    if 'date' in df.columns:
                        df['date'] = pd.to_datetime(df['date'], errors='coerce').dt.date
                        if start:
                            df = df[df['date'] >= start]
                        if end:
                            df = df[df['date'] <= end]
                    return df
            except Exception as e:
                print(f"⚠️ Could not load {name}: {e}")
                return pd.DataFrame()

        food_df = load_csv('Food Log.csv')
        # Rename columns to match the food_log table schema
        food_df = food_df.rename(columns={
            'date': 'log_date',
            'name': 'name',
            'meal': 'meal',
            'calories': 'calories',
            'fat_g': 'fat_g',
            'protein_g': 'protein_g',
            'carbohydrates_g': 'carbs_g',
            'sugar_g': 'sugars_g',
            'fiber_g': 'fiber_g',
            'sodium_mg': 'sodium_mg'
        })

        inserts = {}
        inserts['food_log'] = insert_df(
            food_df,
            'food_log',
            ['log_date', 'name', 'meal', 'calories', 'fat_g', 'protein_g', 'carbs_g', 'sugars_g', 'fiber_g', 'sodium_mg']
        )

        print("\n📊 Ingestion Summary from Lose It ZIP:")
        for table, count in inserts.items():
            print(f"{table:<20}: {count} rows inserted")

def ingest_bloodsugar_csv(csv_path):
    df = pd.read_csv(csv_path)
    df.columns = [normalize_col(c) for c in df.columns]
    df['datetime'] = pd.to_datetime(df['date'] + ' ' + df['time'], errors='coerce')
    df = df.dropna(subset=['datetime', 'blood_glucose_mg_dl'])

    df['reading_time'] = df['datetime']
    df['glucose_value'] = df['blood_glucose_mg_dl']
    df['reading_context'] = df['meal_tag']
    df['meal_relation'] = df['meal_tag'].str.extract(r'\b(after|before)\s+(\w+)', expand=True).apply(lambda x: x[1] if isinstance(x[1], str) else None, axis=1)
    df['feeling_tag'] = df['feeling_tag']
    df['note'] = df.get('note', '')

    inserted = insert_df(
        df,
        'blood_glucose',
        ['reading_time', 'glucose_value', 'reading_context', 'meal_relation', 'feeling_tag', 'note']
    )
    print(f"\n🩸 Blood Glucose: {inserted} rows inserted")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--start', help='Start date YYYY-MM-DD')
    parser.add_argument('--end', help='End date YYYY-MM-DD')
    args = parser.parse_args()

    start = datetime.strptime(args.start, '%Y-%m-%d').date() if args.start else None
    end = datetime.strptime(args.end, '%Y-%m-%d').date() if args.end else None

    if not LOSEIT_ZIP_PATH or not BLOODSUGAR_CSV_PATH:
        print("❌ LOSEIT_ZIP_PATH or BLOODSUGAR_CSV_PATH not set in .env")
        return

    ingest_loseit_zip(LOSEIT_ZIP_PATH, start, end)
    ingest_bloodsugar_csv(BLOODSUGAR_CSV_PATH)

if __name__ == '__main__':
    main()
