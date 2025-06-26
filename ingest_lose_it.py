# ingest_lose_it.py
"""
Script Name: ingest_lose_it.py
Purpose: Ingests food log data from LoseIt ZIP exports into PostgreSQL.
Inputs: ZIP file path from .env or command line
Outputs: Inserted records into the `food_log` table
"""

from pathlib import Path
import os
import getpass
import pandas as pd
import psycopg2
from dotenv import load_dotenv

load_dotenv()  # reads values from .env
PROJECT_DIR = Path(__file__).parent

DB = dict(
    host=os.getenv("PGHOST", "localhost"),
    dbname=os.getenv("PGDB", "health_data"),
    user=os.getenv("PGUSER", getpass.getuser()),
    password=os.getenv("PGPASS", ""),
)

BATCH = int(os.getenv("BATCH", "10000"))  # rows per bulk insert
TZ = os.getenv("TZ", "UTC")  # fallback time-zone

# Default LoseIt ZIP path from .env
DEFAULT_LOSEIT_PATH = os.getenv("LOSEIT_ZIP_PATH", "")


def connect_db():
    """Establishes a connection to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(**DB)
        return conn
    except psycopg2.Error as e:
        print(f"Error connecting to database: {e}")
        return None


def insert_food_log(conn, df, batch_size=None):
    """
    Inserts LoseIt food data into the food_log table.
    Args:
        conn: psycopg2 database connection
        df: Cleaned pandas DataFrame
    Returns:
        None
    """

    if df.empty:
        print("No LoseIt data to insert.")
        return

    if batch_size is None:
        batch_size = BATCH

    cur = conn.cursor()
    
    # Adjust column mapping based on your actual LoseIt export format
    # You may need to modify these column names to match your ZIP
    insert_query = """
        INSERT INTO food_log (log_date, meal_type, food_item, calories_consumed, 
                             protein_g, carbs_g, fat_g, source)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (log_date, meal_type, food_item) DO NOTHING;
    """
    
    # Prepare records for insertion
    records_to_insert = []
    for _, row in df.iterrows():
        # Handle missing values and convert to appropriate types
        try:
            log_date = pd.to_datetime(row.get('log_date') or row.get('Date'), errors='coerce')
            if pd.isna(log_date):
                print(f"Skipping row due to invalid date: {row}")
                continue
                
            calories = float(row.get('calories_consumed', 0) or row.get('Calories', 0) or 0)
            protein = float(row.get('protein_g', 0) or row.get('Protein', 0) or 0)
            carbs = float(row.get('carbs_g', 0) or row.get('Carbs', 0) or 0)
            fat = float(row.get('fat_g', 0) or row.get('Fat', 0) or 0)
            
            records_to_insert.append((
                log_date.date(),  # Convert to date only
                row.get('meal_type', 'Unknown'),
                row.get('food_item') or row.get('Food', 'Unknown'),
                calories,
                protein,
                carbs,
                fat,
                'LoseIt'
            ))
        except (ValueError, TypeError) as e:
            print(f"Error processing row: {row}, Error: {e}")
            continue

    if not records_to_insert:
        print("No valid food log records to insert after processing.")
        return

    try:
        total_inserted = 0
        for i in range(0, len(records_to_insert), batch_size):
            batch = records_to_insert[i:i + batch_size]
            cur.executemany(insert_query, batch)
            conn.commit()
            total_inserted += len(batch)
            print(f"Inserted batch {i // batch_size + 1} ({len(batch)} records)")

        print(f"Total inserted into food_log: {total_inserted}")

    except Exception as e:
        conn.rollback()
        print(f"Error inserting food log: {e}")
    finally:
        cur.close()


def process_loseit_ZIP(ZIP_path):
    """Process and clean LoseIt ZIP data."""
    try:
        df = pd.read_ZIP(ZIP_path)
        print(f"Loaded {len(df)} rows from {ZIP_path}")
        
        # Display first few rows to understand structure
        print("ZIP columns:", df.columns.tolist())
        print("First few rows:")
        print(df.head())
        
        # Drop rows missing essential data
        initial_count = len(df)
        df = df.dropna(subset=['Date'] if 'Date' in df.columns else df.columns[:1])
        print(f"Dropped {initial_count - len(df)} rows with missing essential data")
        
        # Standardize column names (adjust based on your actual LoseIt export format)
        column_mapping = {
            'Date': 'log_date',
            'Meal': 'meal_type',
            'Food': 'food_item',
            'Calories': 'calories_consumed',
            'Protein (g)': 'protein_g',
            'Carbs (g)': 'carbs_g',
            'Fat (g)': 'fat_g'
        }
        
        # Only rename columns that exist in the DataFrame
        existing_mappings = {k: v for k, v in column_mapping.items() if k in df.columns}
        if existing_mappings:
            df = df.rename(columns=existing_mappings)
            print(f"Renamed columns: {existing_mappings}")
        
        # Convert date column to datetime
        date_col = 'log_date' if 'log_date' in df.columns else df.columns[0]
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        
        # Remove rows with invalid dates
        before_date_filter = len(df)
        df = df.dropna(subset=[date_col])
        print(f"Removed {before_date_filter - len(df)} rows with invalid dates")
        
        # Convert numeric columns, handling errors gracefully
        numeric_cols = ['calories_consumed', 'protein_g', 'carbs_g', 'fat_g']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        return df
        
    except Exception as e:
        print(f"Error processing ZIP file: {e}")
        return pd.DataFrame()


def ingest_loseit(ZIP_path=None, start_date=None, end_date=None):
    """Main function to ingest LoseIt data."""
    if ZIP_path is None:
        ZIP_path = DEFAULT_LOSEIT_PATH
    
    if not ZIP_path:
        print("No LoseIt ZIP path provided. Set LOSEIT_ZIP_PATH in .env or pass ZIP_path parameter.")
        return
    
    ZIP_file = Path(ZIP_path)
    if not ZIP_file.exists():
        print(f"LoseIt ZIP file not found: {ZIP_path}")
        return
    
    print(f"➜ Processing LoseIt data from {ZIP_file.name}...")
    df = process_loseit_ZIP(ZIP_path)
    
    if df.empty:
        print("No data to process after cleaning.")
        return
    
    # Apply date filtering if specified
    if start_date or end_date:
        date_col = 'log_date' if 'log_date' in df.columns else df.columns[0]
        if start_date:
            start_dt = pd.to_datetime(start_date)
            df = df[df[date_col] >= start_dt]
            print(f"Filtered to records from {start_date} onwards: {len(df)} rows")
        if end_date:
            end_dt = pd.to_datetime(end_date)
            df = df[df[date_col] <= end_dt]
            print(f"Filtered to records up to {end_date}: {len(df)} rows")
    
    print("➜ Connecting to PostgreSQL and inserting data...")
    conn = connect_db()
    
    if conn:
        insert_food_log(conn, df)
        conn.close()
        print("✅ LoseIt data insertion process complete.")
    else:
        print("❌ Failed to connect to the database. Data not inserted.")


if __name__ == "__main__":
    import sys
    
    # Allow command line argument for ZIP path
    ZIP_path = sys.argv[1] if len(sys.argv) > 1 else None
    
    try:
        ingest_loseit(ZIP_path)
    except Exception as err:
        print(f"\n⚠️ Error: {err}")
    finally:
        input("\nPress Enter to close.")