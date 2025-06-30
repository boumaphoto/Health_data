
# scale_ingest.py
"""
Ingests smart scale data from a CSV file into the PostgreSQL database.
This script handles data cleaning, unit conversion, and insertion into the
'body_measurements' table.
"""

import os
import sys
import getpass
import pandas as pd
import psycopg2
from pathlib import Path
from dotenv import load_dotenv

# --- Configuration ---
load_dotenv()

# Database connection details
DB_CONFIG = {
    'host': os.getenv("PGHOST", "localhost"),
    'dbname': os.getenv("PGDB", "health_data"),
    'user': os.getenv("PGUSER", getpass.getuser()),
    'password': os.getenv("PGPASS", ""),
    'port': os.getenv("PGPORT", "5432")
}

# Path to the scale's CSV export file
SCALE_CSV_PATH = os.getenv("SCALE_CSV_PATH")

# --- Database Functions ---

def get_db_connection():
    """Establishes and returns a database connection."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except psycopg2.OperationalError as e:
        print(f"❌ Database connection failed: {e}", file=sys.stderr)
        print("💡 Check your .env file and ensure PostgreSQL is running.", file=sys.stderr)
        return None

def insert_scale_data(conn, df):
    """
    Inserts a DataFrame of scale data into the body_measurements table.

    Args:
        conn: Active psycopg2 database connection.
        df (pd.DataFrame): DataFrame containing the cleaned scale data.

    Returns:
        int: The number of rows successfully inserted.
    """
    if df.empty:
        return 0

    # Define the columns to be inserted, matching the DataFrame
    db_columns = [
        'timestamp', 'weight_kg', 'body_fat_percentage', 'muscle_mass_kg',
        'bmi', 'metabolic_age', 'visceral_fat', 'water_percentage',
        'device_id', 'source'
    ]
    
    # Ensure the DataFrame only contains columns that exist in the table
    df_insert = df[[col for col in db_columns if col in df.columns]]

    # Create tuples from the DataFrame rows
    tuples = [tuple(x) for x in df_insert.to_numpy()]

    # Define the SQL query
    cols_str = ', '.join(df_insert.columns)
    placeholders = ', '.join(['%s'] * len(df_insert.columns))
    
    # Use the unique constraint (timestamp, device_id) for conflict resolution
    query = f"""
        INSERT INTO body_measurements ({cols_str})
        VALUES ({placeholders})
        ON CONFLICT (timestamp, device_id) DO NOTHING;
    """

    try:
        with conn.cursor() as cur:
            cur.executemany(query, tuples)
            inserted_count = cur.rowcount
            conn.commit()
            return inserted_count
    except Exception as e:
        print(f"❌ Database insert failed: {e}", file=sys.stderr)
        conn.rollback()
        return 0

# --- Data Processing Functions ---

def normalize_columns(df):
    """Normalizes DataFrame column names for consistency."""
    cols = df.columns.str.lower().str.strip()
    cols = cols.str.replace(' ', '_', regex=False)
    cols = cols.str.replace('[()]', '', regex=True)
    cols = cols.str.replace('%', 'percentage', regex=False)
    df.columns = cols
    return df

def process_scale_csv(file_path):
    """
    Reads, cleans, and transforms the scale CSV data.
    """
    try:
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        print(f"❌ Scale CSV file not found at: {file_path}", file=sys.stderr)
        return None

    df = normalize_columns(df)

    # --- Map columns ---
    # Rename columns from the CSV to our standard database column names
    column_map = {
        'date': 'timestamp',
        'weight_lb': 'weight_kg', # Will be converted
        'body_fat': 'body_fat_percentage',
        'muscle_mass_lb': 'muscle_mass_kg', # Will be converted
        'water': 'water_percentage',
        'visceral_fat_rating': 'visceral_fat'
    }
    df.rename(columns=column_map, inplace=True)

    # --- Data Type Conversion and Cleaning ---
    # Convert date/time to a single timestamp column
    if 'time' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'] + ' ' + df['time'], errors='coerce')
    else:
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
    
    df.dropna(subset=['timestamp'], inplace=True)

    # Convert weight and muscle mass from lbs to kg if they exist
    if 'weight_kg' in df.columns:
        df['weight_kg'] = pd.to_numeric(df['weight_kg'], errors='coerce') * 0.453592
    if 'muscle_mass_kg' in df.columns:
        df['muscle_mass_kg'] = pd.to_numeric(df['muscle_mass_kg'], errors='coerce') * 0.453592

    # Convert other columns to numeric, coercing errors
    numeric_cols = [
        'body_fat_percentage', 'bmi', 'metabolic_age', 
        'visceral_fat', 'water_percentage'
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # Add a source column if it doesn't exist
    if 'source' not in df.columns:
        df['source'] = 'SmartScale'
        
    if 'device_id' not in df.columns:
        df['device_id'] = 'DefaultScale'


    return df

# --- Main Execution ---

def main():
    """Main function to run the scale data ingestion process."""
    print("⚖️  Starting smart scale data ingestion...")

    if not SCALE_CSV_PATH:
        print("❌ Environment variable SCALE_CSV_PATH is not set.", file=sys.stderr)
        print("💡 Please set it in your .env file.", file=sys.stderr)
        return

    # Process the CSV file
    df = process_scale_csv(SCALE_CSV_PATH)
    if df is None or df.empty:
        print("No data to ingest after processing.")
        return

    # Get database connection
    conn = get_db_connection()
    if not conn:
        return

    # Insert data into the database
    try:
        inserted_count = insert_scale_data(conn, df)
        print(f"✅ Successfully inserted {inserted_count} new scale measurements.")
    finally:
        conn.close()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⏹️  Process cancelled by user.")
    except Exception as e:
        print(f"\n💥 An unexpected error occurred: {e}", file=sys.stderr)
