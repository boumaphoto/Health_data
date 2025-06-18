import sys
import zipfile
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path
import pandas as pd
import psycopg2
from psycopg2 import sql
from datetime import datetime

# ------------------------------------------------------------
# 1)  EDIT HERE: Path to your Apple Health export ZIP file
#     Use a raw string (r"...") so back-slashes aren’t escapes.
#     Example: r"/home/your_username/Downloads/Health data 2024-01-01 12_00_00.zip"
# ------------------------------------------------------------
export_zip = Path(
    r"A:/ONEDRIVE/mike/apple health/Health data 5 21 25 2025-05-21 12_10_15.zip"  # <--- UPDATE THIS PATH
)

# Database Connection Details
DB_HOST = "localhost"
DB_NAME = "health_data"
DB_USER = "your_username"  # <--- UPDATE THIS
DB_PASSWORD = "your_secure_password"  # <--- UPDATE THIS


def connect_db():
    """Establishes a connection to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASSWORD)
        return conn
    except psycopg2.Error as e:
        print(f"Error connecting to database: {e}")
        sys.exit(1)


def insert_health_records(conn, data):
    """Inserts a list of health records into the health_records table."""
    if not data:
        return

    cur = conn.cursor()

    # We are relying on the primary key constraint to prevent duplicates if you reload the same data.
    # Alternatively, you could add ON CONFLICT (type, start_date, end_date, value) DO NOTHING;
    # if you added a UNIQUE constraint on these columns in create_db_schema.py,
    # which would be more robust for preventing exact duplicates on re-runs.
    insert_query = """
        INSERT INTO health_records (type, start_date, end_date, value, unit, source_name)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT DO NOTHING; -- Add this to avoid inserting exact duplicates if you define a UNIQUE constraint in schema
    """
    records_to_insert = []
    for record in data:
        try:
            value = float(record.get("value")) if record.get("value") else None
        except ValueError:
            value = None  # Handle non-numeric values

        # Ensure timestamps are parsed correctly, handling potential NaT for invalid dates
        start_date = pd.to_datetime(record.get("startDate"), errors='coerce')
        end_date = pd.to_datetime(record.get("endDate"), errors='coerce')

        # Only add if dates are valid
        if pd.isna(start_date) or pd.isna(end_date):
            print(f"Skipping record due to invalid date: {record}")
            continue

        records_to_insert.append((
            record.get("type"),
            start_date,
            end_date,
            value,
            record.get("unit"),
            record.get("source"),
        ))

    if not records_to_insert:
        print("No valid quantity records to insert after parsing and date validation.")
        return

    try:
        cur.executemany(insert_query, records_to_insert)
        conn.commit()
        print(f"Inserted {len(records_to_insert)} quantity records into health_records.")
    except Exception as e:
        conn.rollback()
        print(f"Error inserting health quantity records: {e}")
    finally:
        cur.close()


def insert_health_category_records(conn, data):
    """Inserts a list of health category records into the health_category_records table."""
    if not data:
        return

    cur = conn.cursor()
    insert_query = """
        INSERT INTO health_category_records (type, start_date, end_date, value, source_name)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT DO NOTHING; -- Add this if you define a UNIQUE constraint in schema
    """
    records_to_insert = []
    for record in data:
        start_date = pd.to_datetime(record.get("startDate"), errors='coerce')
        end_date = pd.to_datetime(record.get("endDate"), errors='coerce')

        if pd.isna(start_date) or pd.isna(end_date):
            print(f"Skipping category record due to invalid date: {record}")
            continue

        records_to_insert.append((
            record.get("type"),
            start_date,
            end_date,
            record.get("value"),
            record.get("source"),
        ))

    if not records_to_insert:
        print("No valid category records to insert after parsing and date validation.")
        return

    try:
        cur.executemany(insert_query, records_to_insert)
        conn.commit()
        print(f"Inserted {len(records_to_insert)} category records into health_category_records.")
    except Exception as e:
        conn.rollback()
        print(f"Error inserting health category records: {e}")
    finally:
        cur.close()


def insert_workouts(conn, data):
    """Inserts a list of workout records into the workouts table."""
    if not data:
        return

    cur = conn.cursor()
    insert_query = """
        INSERT INTO workouts (activity_type, start_date, end_date, duration_seconds, total_distance, distance_unit, total_energy_burned, energy_unit, source_name)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT DO NOTHING; -- Add this if you define a UNIQUE constraint in schema
    """
    records_to_insert = []
    for record in data:
        start_date = pd.to_datetime(record.get("startDate"), errors='coerce')
        end_date = pd.to_datetime(record.get("endDate"), errors='coerce')

        if pd.isna(start_date) or pd.isna(end_date):
            print(f"Skipping workout record due to invalid date: {record}")
            continue

        # Convert values, handling potential None or ValueError
        duration_s = float(record.get("duration", 0)) if record.get("duration") else None
        distance = float(record.get("totalDistance", 0)) if record.get("totalDistance") else None
        energy = float(record.get("totalEnergyBurned", 0)) if record.get("totalEnergyBurned") else None

        records_to_insert.append((
            record.get("workoutActivityType"),
            start_date,
            end_date,
            duration_s,
            distance,
            record.get("totalDistanceUnit"),
            energy,
            record.get("totalEnergyBurnedUnit"),
            record.get("sourceName"),
        ))

    if not records_to_insert:
        print("No valid workout records to insert after parsing and date validation.")
        return

    try:
        cur.executemany(insert_query, records_to_insert)
        conn.commit()
        print(f"Inserted {len(records_to_insert)} workout records into workouts.")
    except Exception as e:
        conn.rollback()
        print(f"Error inserting workouts: {e}")
    finally:
        cur.close()


def main(zip_path: Path):
    if not zip_path.is_file():
        raise FileNotFoundError(f"Zip file not found: {zip_path}")

    extract_folder = zip_path.with_suffix("")
    extract_folder.mkdir(exist_ok=True)

    print("➜  Unzipping export …")
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(extract_folder)

    try:
        export_xml = next(
            p for p in extract_folder.rglob("export.xml")
            if p.name.lower() == "export.xml"
        )
    except StopIteration:
        raise FileNotFoundError(
            f"'export.xml' not found anywhere inside {zip_path.name}"
        )

    print(f"➜  Parsing {export_xml.relative_to(extract_folder)} … "
          "(large files can take a minute)")

    tree = ET.parse(export_xml)
    root = tree.getroot()

    health_quantity_data = []
    health_category_data = []
    workout_data = []

    for elem in root:
        if elem.tag == "Record":
            if elem.get("type", "").startswith("HKQuantityTypeIdentifier"):
                health_quantity_data.append(
                    {
                        "type": elem.get("type"),
                        "startDate": elem.get("startDate"),
                        "endDate": elem.get("endDate"),
                        "value": elem.get("value"),
                        "unit": elem.get("unit"),
                        "source": elem.get("sourceName"),
                    }
                )
            elif elem.get("type", "").startswith("HKCategoryTypeIdentifier"):
                health_category_data.append(
                    {
                        "type": elem.get("type"),
                        "startDate": elem.get("startDate"),
                        "endDate": elem.get("endDate"),
                        "value": elem.get("value"),  # For category, value might be 'inBed', 'asleepCore' etc.
                        "source": elem.get("sourceName"),
                    }
                )
        elif elem.tag == "Workout":
            workout_data.append(
                {
                    "workoutActivityType": elem.get("workoutActivityType"),
                    "startDate": elem.get("startDate"),
                    "endDate": elem.get("endDate"),
                    "duration": elem.get("duration"),
                    "durationUnit": elem.get("durationUnit"),
                    "totalDistance": elem.get("totalDistance"),
                    "totalDistanceUnit": elem.get("totalDistanceUnit"),
                    "totalEnergyBurned": elem.get("totalEnergyBurned"),
                    "totalEnergyBurnedUnit": elem.get("totalEnergyBurnedUnit"),
                    "sourceName": elem.get("sourceName"),
                    # Add other workout attributes if needed, e.g., totalFlightsClimbed, totalSwimmingStrokeCount
                }
            )

    print("➜  Connecting to PostgreSQL and inserting data...")
    conn = connect_db()
    if conn:
        insert_health_records(conn, health_quantity_data)
        insert_health_category_records(conn, health_category_data)  # This line should now be uncommented
        insert_workouts(conn, workout_data)  # This line should now be uncommented

        conn.close()
        print("✅  Data insertion process complete.")
    else:
        print("❌  Failed to connect to the database. Data not inserted.")


if __name__ == "__main__":
    try:
        main(export_zip)
    except Exception as err:
        print("\n⚠️  Error:", err)
    finally:
        input("\nPress Enter to close.")