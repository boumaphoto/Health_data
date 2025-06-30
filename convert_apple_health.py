# improved_convert_apple_health.py
"""
Enhanced Apple Health Data Import Script

This script extracts health data from Apple Health exports and imports it into PostgreSQL.
It includes better error handling, progress tracking, and data validation.
"""

import sys
import zipfile
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path
import pandas as pd
import psycopg2
from psycopg2 import sql
from datetime import datetime
import os
import getpass
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Centralized database configuration - matches the schema script
DB_CONFIG = {
    'host': os.getenv("PGHOST", "localhost"),
    'dbname': os.getenv("PGDB", "health_data"),
    'user': os.getenv("PGUSER", getpass.getuser()),
    'password': os.getenv("PGPASS", ""),
    'port': os.getenv("PGPORT", "5432")
}

# Configure your Apple Health export path here
export_path_str = os.getenv("APPLE_HEALTH_ZIP_PATH")
if not export_path_str:
    print("❌ APPLE_HEALTH_ZIP_PATH is not set in your .env file.")
    sys.exit(1)

EXPORT_ZIP_PATH = Path(export_path_str)

# Batch size for database inserts
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "1000"))

def get_db_connection():
    """Creates a database connection with proper error handling."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except psycopg2.OperationalError as e:
        print(f"❌ Database connection failed: {e}")
        print("💡 Check your .env file and ensure PostgreSQL is running")
        return None
    except Exception as e:
        print(f"❌ Unexpected database error: {e}")
        return None

def validate_and_parse_timestamp(timestamp_str):
    """Validates and parses Apple Health timestamp strings."""
    if not timestamp_str:
        return None
    try:
        return pd.to_datetime(timestamp_str, errors='coerce')
    except Exception:
        return None

def parse_numeric_value(value_str):
    """Safely converts string values to numeric."""
    if not value_str or value_str.strip() == '':
        return None
    try:
        return float(value_str)
    except (ValueError, TypeError):
        return None

def insert_batch(conn, table_name, columns, data_batch):
    """Inserts a batch of records with conflict resolution."""
    if not data_batch:
        return 0
    
    with conn.cursor() as cur:
        try:
            values_placeholder = ",".join(["%s"] * len(columns))
            conflict_columns = ",".join(columns)
            
            insert_query = sql.SQL("""
                INSERT INTO {table} ({cols}) VALUES ({placeholders})
                ON CONFLICT ({conflict_cols}) DO NOTHING;
            """).format(
                table=sql.Identifier(table_name),
                cols=sql.SQL(", ").join(map(sql.Identifier, columns)),
                placeholders=sql.SQL(values_placeholder),
                conflict_cols=sql.SQL(conflict_columns)
            )

            # executemany is not supported with sql.SQL, so we use a loop with execute
            # This is less efficient but necessary for dynamic table/column names
            # For performance, consider separate functions if the schema is stable
            for record in data_batch:
                cur.execute(insert_query, record)

            inserted_count = cur.rowcount
            conn.commit()
            return inserted_count
        except Exception as e:
            conn.rollback()
            print(f"⚠️  Error inserting batch into {table_name}: {e}")
            return 0

def process_apple_health_export(zip_path: Path):
    """Main function to process Apple Health export."""
    if not zip_path.exists():
        print(f"❌ Export file not found: {zip_path}")
        return False
    
    extract_folder = zip_path.with_suffix("")
    extract_folder.mkdir(exist_ok=True)
    
    print(f"📦 Extracting {zip_path.name}...")
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(extract_folder)
    except Exception as e:
        print(f"❌ Error extracting ZIP file: {e}")
        return False
    
    try:
        export_xml = next(p for p in extract_folder.rglob("export.xml") if p.name.lower() == "export.xml")
    except StopIteration:
        print(f"❌ 'export.xml' not found in {zip_path.name}")
        return False
    
    print(f"📊 Parsing {export_xml.name}...")
    
    try:
        tree = ET.parse(export_xml)
        root = tree.getroot()
    except Exception as e:
        print(f"❌ Error parsing XML file: {e}")
        return False
    
    health_quantity_data = []
    health_category_data = []
    workout_data = []
    
    total_records = len(root)
    processed_records = 0
    
    conn = get_db_connection()
    if not conn:
        return False
    
    print(f"🔄 Processing {total_records:,} records...")
    
    try:
        for elem in root:
            processed_records += 1
            if processed_records % 10000 == 0:
                progress_pct = (processed_records / total_records) * 100
                print(f"   Progress: {processed_records:,}/{total_records:,} ({progress_pct:.1f}%)")
            
            if elem.tag == "Record":
                record_type = elem.get("type", "")
                start_date = validate_and_parse_timestamp(elem.get("startDate"))
                end_date = validate_and_parse_timestamp(elem.get("endDate"))

                if not start_date or not end_date:
                    continue

                record = {
                    "type": record_type,
                    "source_name": elem.get("sourceName"),
                    "source_version": elem.get("sourceVersion"),
                    "device": elem.get("device"),
                    "unit": elem.get("unit"),
                    "creation_date": validate_and_parse_timestamp(elem.get("creationDate")),
                    "start_date": start_date,
                    "end_date": end_date,
                    "value": elem.get("value")
                }

                if record_type.startswith("HKQuantityTypeIdentifier"):
                    health_quantity_data.append(record)
                elif record_type.startswith("HKCategoryTypeIdentifier"):
                    health_category_data.append(record)
            
            elif elem.tag == "Workout":
                start_date = validate_and_parse_timestamp(elem.get("startDate"))
                end_date = validate_and_parse_timestamp(elem.get("endDate"))

                if not start_date or not end_date:
                    continue

                workout_data.append({
                    "activity_name": elem.get("workoutActivityType"),
                    "duration": parse_numeric_value(elem.get("duration")),
                    "duration_unit": elem.get("durationUnit"),
                    "total_distance": parse_numeric_value(elem.get("totalDistance")),
                    "total_distance_unit": elem.get("totalDistanceUnit"),
                    "total_energy_burned": parse_numeric_value(elem.get("totalEnergyBurned")),
                    "total_energy_burned_unit": elem.get("totalEnergyBurnedUnit"),
                    "source_name": elem.get("sourceName"),
                    "source_version": elem.get("sourceVersion"),
                    "device": elem.get("device"),
                    "creation_date": validate_and_parse_timestamp(elem.get("creationDate")),
                    "start_date": start_date,
                    "end_date": end_date
                })
            
            if len(health_quantity_data) >= BATCH_SIZE:
                insert_batch(conn, 'health_records', list(health_quantity_data[0].keys()), [list(d.values()) for d in health_quantity_data])
                health_quantity_data = []
            
            if len(health_category_data) >= BATCH_SIZE:
                insert_batch(conn, 'health_category_records', list(health_category_data[0].keys()), [list(d.values()) for d in health_category_data])
                health_category_data = []
            
            if len(workout_data) >= BATCH_SIZE:
                insert_batch(conn, 'workouts', list(workout_data[0].keys()), [list(d.values()) for d in workout_data])
                workout_data = []
        
        if health_quantity_data:
            insert_batch(conn, 'health_records', list(health_quantity_data[0].keys()), [list(d.values()) for d in health_quantity_data])
        
        if health_category_data:
            insert_batch(conn, 'health_category_records', list(health_category_data[0].keys()), [list(d.values()) for d in health_category_data])
        
        if workout_data:
            insert_batch(conn, 'workouts', list(workout_data[0].keys()), [list(d.values()) for d in workout_data])
        
        print("🎉 Apple Health data import completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error processing health data: {e}")
        return False
    finally:
        if conn:
            conn.close()

def main():
    """Main entry point for the script."""
    print("🍎 Apple Health Data Import Tool")
    if not EXPORT_ZIP_PATH.exists():
        print(f"❌ Export file not found: {EXPORT_ZIP_PATH}")
        return
    
    conn = get_db_connection()
    if conn:
        conn.close()
        print("✅ Database connection successful")
    else:
        print("❌ Database connection failed")
        return
    
    success = process_apple_health_export(EXPORT_ZIP_PATH)
    
    if success:
        print("\n🎉 Import completed successfully!")
    else:
        print("\n❌ Import failed.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⏹️  Import cancelled by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
