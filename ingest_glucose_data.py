# ingest_glucose_data.py

import os
import pandas as pd
import psycopg2
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

DB_CONFIG = {
    'host': os.getenv("PGHOST", "localhost"),
    'dbname': os.getenv("PGDB", "health_data"),
    'user': os.getenv("PGUSER", os.getlogin()),
    'password': os.getenv("PGPASS", ""),
    'port': os.getenv("PGPORT", "5432")
}

DEFAULT_GLUCOSE_CSV = os.getenv("BLOODSUGAR_CSV_PATH", "")

def get_db_connection():
    try:
        return psycopg2.connect(**DB_CONFIG)
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return None

def ingest_glucose_data(csv_path=None):
    if csv_path is None:
        csv_path = DEFAULT_GLUCOSE_CSV

    if not csv_path or not os.path.exists(csv_path):
        print(f"⚠️ Glucose CSV not found: {csv_path}")
        return

    df = pd.read_csv(csv_path)
    df['datetime'] = pd.to_datetime(df['date'] + ' ' + df['time'], errors='coerce')
    df = df.dropna(subset=['datetime', 'Blood Glucose (mg/dL)'])

    df['reading_time'] = df['datetime']
    df['glucose_value'] = df['Blood Glucose (mg/dL)']
    df['reading_context'] = df['Meal Tag']
    df['meal_relation'] = df['Meal Tag'].str.extract(r'\b(after|before)\s+(\w+)', expand=True).apply(lambda x: x[1] if isinstance(x[1], str) else None, axis=1)
    df['notes'] = df.get('Note', '')

    cols = ['reading_time', 'glucose_value', 'reading_context', 'meal_relation', 'notes']
    df = df[cols]

    conn = get_db_connection()
    if conn is None:
        return

    cur = conn.cursor()
    insert_query = """
        INSERT INTO blood_glucose_meter (reading_time, glucose_value, reading_context, meal_relation, notes)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT DO NOTHING;
    """
    try:
        rows = [tuple(x) for x in df.to_numpy()]
        cur.executemany(insert_query, rows)
        conn.commit()
        print(f"Inserted {cur.rowcount} glucose records")
    except Exception as e:
        conn.rollback()
        print(f"Insert failed: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    ingest_glucose_data()
