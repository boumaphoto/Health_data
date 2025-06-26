# check_table_counts.py
    # Python script you can run to connect to your database and check how much data is in each table.
    
import os
import psycopg2
from dotenv import load_dotenv

# Load .env file
load_dotenv()

DB_CONFIG = {
    'host': os.getenv("PGHOST", "localhost"),
    'dbname': os.getenv("PGDB", "health_data"),
    'user': os.getenv("PGUSER", "postgres"),
    'password': os.getenv("PGPASS", ""),
    'port': os.getenv("PGPORT", "5432")
}

TABLES = [
    "health_records",
    "health_category_records",
    "workouts",
    "food_log",
    "body_measurements",
    "blood_glucose_meter"
]

def get_table_counts():
    try:
        with psycopg2.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cur:
                print("📊 Table row counts:")
                for table in TABLES:
                    try:
                        cur.execute(f"SELECT COUNT(*) FROM {table};")
                        count = cur.fetchone()[0]
                        print(f"  {table:<25}: {count} rows")
                    except Exception as e:
                        print(f"  {table:<25}: ❌ ERROR - {e}")
    except Exception as conn_err:
        print(f"❌ Could not connect to database: {conn_err}")

if __name__ == "__main__":
    get_table_counts()
