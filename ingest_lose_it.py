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

# load_loseit_data.py
import pandas as pd
import psycopg2
from datetime import datetime

# DB connection details (same as above)
DB_HOST = "localhost" 
DB_NAME = "health_data"
DB_USER = "your_username"
DB_PASSWORD = "your_secure_password"

def connect_db():
    # Same connect_db function as above
    pass

def insert_food_log(conn, df):
    """Inserts DataFrame into food_log table."""
    if df.empty:
        print("No LoseIt data to insert.")
        return

    cur = conn.cursor()
    # Assuming 'log_date', 'meal_type', 'food_item', 'calories_consumed', 'protein_g', 'carbs_g', 'fat_g'
    # columns exist in your DataFrame. Adjust as per actual LoseIt export.
    insert_query = """
        INSERT INTO food_log (log_date, meal_type, food_item, calories_consumed, protein_g, carbs_g, fat_g, source)
        VALUES (%s, %s, %s, %s, %s, %s, %s, 'LoseIt')
        ON CONFLICT (log_date, meal_type, food_item) DO NOTHING; -- Requires UNIQUE constraint on these columns
    """
    records_to_insert = df[['log_date', 'meal_type', 'food_item', 'calories_consumed', 'protein_g', 'carbs_g', 'fat_g']].values.tolist()

    try:
        cur.executemany(insert_query, records_to_insert)
        conn.commit()
        print(f"Inserted {len(records_to_insert)} records into food_log.")
    except Exception as e:
        conn.rollback()
        print(f"Error inserting food log: {e}")
    finally:
        cur.close()

def main_loseit(loseit_export_path):
    # Determine export format (CSV, JSON etc.)
    # Example for CSV:
    df = pd.read_csv(loseit_export_path)
    
    # Perform cleaning and transformation:
    # - Rename columns to match DB schema (e.g., 'Date' -> 'log_date')
    # - Convert date columns to datetime objects: pd.to_datetime(df['Date'])
    # - Convert numeric columns: pd.to_numeric(df['Calories'], errors='coerce')
    # - Handle any missing data
    
    conn = connect_db()
    if conn:
        insert_food_log(conn, df)
        conn.close()

if __name__ == "__main__":
    # Replace with actual path to your LoseIt export
    # main_loseit("path/to/your/loseit_export.csv") 
    print("Run `main_loseit()` with your LoseIt export file path.")
