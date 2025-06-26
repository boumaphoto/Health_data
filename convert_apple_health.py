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
# Use forward slashes or raw strings to avoid path issues on Windows
export_path_str = os.getenv("APPLE_HEALTH_ZIP_PATH")
if not export_path_str:
    print("❌ APPLE_HEALTH_ZIP_PATH is not set in your .env file.")
    sys.exit(1)

EXPORT_ZIP_PATH = Path(export_path_str)




# Batch size for database inserts - helps with memory management
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "1000"))

def get_db_connection():
    """
    Creates a database connection with proper error handling.
    This function centralizes connection logic and provides helpful error messages.
    """
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
    """
    Validates and parses Apple Health timestamp strings.
    Apple Health uses ISO format, but we need to handle potential parsing errors.
    
    Args:
        timestamp_str: String timestamp from Apple Health XML
        
    Returns:
        pandas.Timestamp or None if parsing fails
    """
    if not timestamp_str:
        return None
    
    try:
        # Apple Health uses ISO format like "2024-01-15 10:30:00 -0500"
        parsed_time = pd.to_datetime(timestamp_str, errors='coerce')
        return parsed_time if not pd.isna(parsed_time) else None
    except Exception:
        return None

def parse_numeric_value(value_str):
    """
    Safely converts string values to numeric, handling various edge cases.
    
    Args:
        value_str: String representation of a number
        
    Returns:
        float or None if conversion fails
    """
    if not value_str or value_str.strip() == '':
        return None
    
    try:
        return float(value_str)
    except (ValueError, TypeError):
        return None

def insert_health_records_batch(conn, records_batch):
    """
    Inserts a batch of health records with proper error handling and conflict resolution.
    
    Args:
        conn: Database connection
        records_batch: List of health record dictionaries
        
    Returns:
        int: Number of records successfully inserted
    """
    if not records_batch:
        return 0
    
    cur = conn.cursor()
    
    # Prepare the insert query with conflict handling
    insert_query = """
        INSERT INTO health_records (type, start_date, end_date, value, unit, source_name)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (type, start_date, end_date, value, source_name) DO NOTHING;
    """
    
    # Process and validate each record
    valid_records = []
    for record in records_batch:
        # Validate required fields
        start_date = validate_and_parse_timestamp(record.get("startDate"))
        end_date = validate_and_parse_timestamp(record.get("endDate"))
        
        if not start_date or not end_date:
            continue  # Skip records with invalid dates
        
        # Parse numeric value
        numeric_value = parse_numeric_value(record.get("value"))
        
        # Only include records with valid data
        if record.get("type") and numeric_value is not None:
            valid_records.append((
                record.get("type"),
                start_date,
                end_date,
                numeric_value,
                record.get("unit"),
                record.get("source", "Apple Health")
            ))
    
    if not valid_records:
        cur.close()
        return 0
    
    try:
        cur.executemany(insert_query, valid_records)
        inserted_count = cur.rowcount
        conn.commit()
        cur.close()
        return inserted_count
    except Exception as e:
        conn.rollback()
        cur.close()
        print(f"⚠️  Error inserting health records batch: {e}")
        return 0

def insert_category_records_batch(conn, records_batch):
    """
    Inserts a batch of category records (like sleep data) with validation.
    
    Args:
        conn: Database connection
        records_batch: List of category record dictionaries
        
    Returns:
        int: Number of records successfully inserted
    """
    if not records_batch:
        return 0
    
    cur = conn.cursor()
    
    insert_query = """
        INSERT INTO health_category_records (type, start_date, end_date, value, source_name)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (type, start_date, end_date, value, source_name) DO NOTHING;
    """
    
    valid_records = []
    for record in records_batch:
        start_date = validate_and_parse_timestamp(record.get("startDate"))
        end_date = validate_and_parse_timestamp(record.get("endDate"))
        
        if start_date and end_date and record.get("type"):
            valid_records.append((
                record.get("type"),
                start_date,
                end_date,
                record.get("value", ""),
                record.get("source", "Apple Health")
            ))
    
    if not valid_records:
        cur.close()
        return 0
    
    try:
        cur.executemany(insert_query, valid_records)
        inserted_count = cur.rowcount
        conn.commit()
        cur.close()
        return inserted_count
    except Exception as e:
        conn.rollback()
        cur.close()
        print(f"⚠️  Error inserting category records batch: {e}")
        return 0

def insert_workouts_batch(conn, workouts_batch):
    """
    Inserts a batch of workout records with comprehensive data validation.
    
    Args:
        conn: Database connection
        workouts_batch: List of workout dictionaries
        
    Returns:
        int: Number of workouts successfully inserted
    """
    if not workouts_batch:
        return 0
    
    cur = conn.cursor()
    
    insert_query = """
        INSERT INTO workouts (
            activity_type, start_date, end_date, duration_seconds, 
            total_distance, distance_unit, total_energy_burned, energy_unit, source_name
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (activity_type, start_date, end_date, source_name) DO NOTHING;
    """
    
    valid_workouts = []
    for workout in workouts_batch:
        start_date = validate_and_parse_timestamp(workout.get("startDate"))
        end_date = validate_and_parse_timestamp(workout.get("endDate"))
        
        if not start_date or not end_date or not workout.get("workoutActivityType"):
            continue
        
        # Calculate duration if not provided
        duration_seconds = parse_numeric_value(workout.get("duration"))
        if not duration_seconds and start_date and end_date:
            duration_seconds = (end_date - start_date).total_seconds()
        
        valid_workouts.append((
            workout.get("workoutActivityType"),
            start_date,
            end_date,
            duration_seconds,
            parse_numeric_value(workout.get("totalDistance")),
            workout.get("totalDistanceUnit"),
            parse_numeric_value(workout.get("totalEnergyBurned")),
            workout.get("totalEnergyBurnedUnit"),
            workout.get("sourceName", "Apple Health")
        ))
    
    if not valid_workouts:
        cur.close()
        return 0
    
    try:
        cur.executemany(insert_query, valid_workouts)
        inserted_count = cur.rowcount
        conn.commit()
        cur.close()
        return inserted_count
    except Exception as e:
        conn.rollback()
        cur.close()
        print(f"⚠️  Error inserting workouts batch: {e}")
        return 0

def process_apple_health_export(zip_path: Path):
    """
    Main function to process Apple Health export with progress tracking and batch processing.
    
    This function extracts the ZIP file, parses the XML, and imports data in batches
    to handle large files efficiently and provide progress feedback.
    
    Args:
        zip_path: Path to the Apple Health export ZIP file
    """
    if not zip_path.exists():
        print(f"❌ Export file not found: {zip_path}")
        print(f"💡 Please update EXPORT_ZIP_PATH in the script or set APPLE_HEALTH_EXPORT environment variable")
        return False
    
    # Create extraction directory
    extract_folder = zip_path.with_suffix("")
    extract_folder.mkdir(exist_ok=True)
    
    print(f"📦 Extracting {zip_path.name}...")
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(extract_folder)
    except Exception as e:
        print(f"❌ Error extracting ZIP file: {e}")
        return False
    
    # Find the export.xml file
    try:
        export_xml = next(
            p for p in extract_folder.rglob("export.xml")
            if p.name.lower() == "export.xml"
        )
    except StopIteration:
        print(f"❌ 'export.xml' not found in {zip_path.name}")
        return False
    
    print(f"📊 Parsing {export_xml.name}...")
    print("⏳ This may take several minutes for large files...")
    
    # Parse XML with progress tracking
    try:
        tree = ET.parse(export_xml)
        root = tree.getroot()
    except Exception as e:
        print(f"❌ Error parsing XML file: {e}")
        return False
    
    # Initialize data collections and counters
    health_quantity_data = []
    health_category_data = []
    workout_data = []
    
    total_records = len(root)
    processed_records = 0
    
    # Connect to database
    conn = get_db_connection()
    if not conn:
        return False
    
    # Process XML elements with batch insertion
    print(f"🔄 Processing {total_records:,} records...")
    
    try:
        for elem in root:
            processed_records += 1
            
            # Show progress every 10,000 records
            if processed_records % 10000 == 0:
                progress_pct = (processed_records / total_records) * 100
                print(f"   Progress: {processed_records:,}/{total_records:,} ({progress_pct:.1f}%)")
            
            # Process different types of health records
            if elem.tag == "Record":
                record_type = elem.get("type", "")
                
                if record_type.startswith("HKQuantityTypeIdentifier"):
                    health_quantity_data.append({
                        "type": record_type,
                        "startDate": elem.get("startDate"),
                        "endDate": elem.get("endDate"),
                        "value": elem.get("value"),
                        "unit": elem.get("unit"),
                        "source": elem.get("sourceName", "Apple Health"),
                    })
                    
                elif record_type.startswith("HKCategoryTypeIdentifier"):
                    health_category_data.append({
                        "type": record_type,
                        "startDate": elem.get("startDate"),
                        "endDate": elem.get("endDate"),
                        "value": elem.get("value"),
                        "source": elem.get("sourceName", "Apple Health"),
                    })
            
            elif elem.tag == "Workout":
                workout_data.append({
                    "workoutActivityType": elem.get("workoutActivityType"),
                    "startDate": elem.get("startDate"),
                    "endDate": elem.get("endDate"),
                    "duration": elem.get("duration"),
                    "durationUnit": elem.get("durationUnit"),
                    "totalDistance": elem.get("totalDistance"),
                    "totalDistanceUnit": elem.get("totalDistanceUnit"),
                    "totalEnergyBurned": elem.get("totalEnergyBurned"),
                    "totalEnergyBurnedUnit": elem.get("totalEnergyBurnedUnit"),
                    "sourceName": elem.get("sourceName", "Apple Health"),
                })
            
            # Process batches when they reach the configured size
            if len(health_quantity_data) >= BATCH_SIZE:
                inserted = insert_health_records_batch(conn, health_quantity_data)
                print(f"   ✅ Inserted {inserted} health records")
                health_quantity_data = []
            
            if len(health_category_data) >= BATCH_SIZE:
                inserted = insert_category_records_batch(conn, health_category_data)
                print(f"   ✅ Inserted {inserted} category records")
                health_category_data = []
            
            if len(workout_data) >= BATCH_SIZE:
                inserted = insert_workouts_batch(conn, workout_data)
                print(f"   ✅ Inserted {inserted} workouts")
                workout_data = []
        
        # Process any remaining records
        if health_quantity_data:
            inserted = insert_health_records_batch(conn, health_quantity_data)
            print(f"✅ Final batch: {inserted} health records")
        
        if health_category_data:
            inserted = insert_category_records_batch(conn, health_category_data)
            print(f"✅ Final batch: {inserted} category records")
        
        if workout_data:
            inserted = insert_workouts_batch(conn, workout_data)
            print(f"✅ Final batch: {inserted} workouts")
        
        print("🎉 Apple Health data import completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error processing health data: {e}")
        return False
    finally:
        if conn:
            conn.close()

def main():
    """
    Main entry point for the Apple Health import script.
    """
    print("🍎 Apple Health Data Import Tool")
    print("=" * 40)
    
    # Validate configuration
    if not EXPORT_ZIP_PATH.exists():
        print(f"❌ Export file not found: {EXPORT_ZIP_PATH}")
        print("\n💡 To fix this:")
        print("1. Export your health data from the Apple Health app")
        print("2. Save the export.zip file to your computer")  
        print("3. Update EXPORT_ZIP_PATH in this script or set APPLE_HEALTH_EXPORT environment variable")
        return
    
    # Test database connection
    print("🔍 Testing database connection...")
    conn = get_db_connection()
    if conn:
        conn.close()
        print("✅ Database connection successful")
    else:
        print("❌ Database connection failed")
        return
    
    # Process the export
    success = process_apple_health_export(EXPORT_ZIP_PATH)
    
    if success:
        print("\n🎉 Import completed successfully!")
        print("You can now analyze your Apple Health data in the database.")
    else:
        print("\n❌ Import failed. Please check the error messages above.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⏹️  Import cancelled by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
    finally:
        input("\nPress Enter to close...")