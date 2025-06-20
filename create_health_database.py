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

import psycopg2
from psycopg2 import sql
from datetime import datetime

DB_HOST = "localhost"  # Or your computers IP if running on Windows
DB_NAME = "health_data"
DB_USER = "your_username" # <--- UPDATE THIS
DB_PASSWORD = "your_secure_password" # <--- UPDATE THIS

def create_tables():
    conn = None
    try:
        conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASSWORD)
        cur = conn.cursor()

        # health_records table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS health_records (
                record_id BIGSERIAL PRIMARY KEY,
                type VARCHAR(100) NOT NULL,
                start_date TIMESTAMP WITH TIME ZONE NOT NULL,
                end_date TIMESTAMP WITH TIME ZONE NOT NULL,
                value NUMERIC(10, 4),
                unit VARCHAR(50),
                source_name VARCHAR(100),
                creation_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (type, start_date, end_date, value)
            );
        """)
        print("Table 'health_records' ensured.")

        # health_category_records table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS health_category_records (
                record_id BIGSERIAL PRIMARY KEY,
                type VARCHAR(100) NOT NULL,
                start_date TIMESTAMP WITH TIME ZONE NOT NULL,
                end_date TIMESTAMP WITH TIME ZONE NOT NULL,
                value VARCHAR(50), -- Category values like 'inBed'
                source_name VARCHAR(100),
                creation_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """)
        print("Table 'health_category_records' ensured.")

        # workouts table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS workouts (
                workout_id BIGSERIAL PRIMARY KEY,
                activity_type VARCHAR(100) NOT NULL,
                start_date TIMESTAMP WITH TIME ZONE NOT NULL,
                end_date TIMESTAMP WITH TIME ZONE NOT NULL,
                duration_seconds NUMERIC(10, 2),
                total_distance NUMERIC(10, 4),
                distance_unit VARCHAR(50),
                total_energy_burned NUMERIC(10, 2),
                energy_unit VARCHAR(50),
                source_name VARCHAR(100),
                creation_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """)
        print("Table 'workouts' ensured.")

        # food_log table (adjust columns based on your LoseIt export)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS food_log (
                log_id BIGSERIAL PRIMARY KEY,
                log_date DATE NOT NULL,
                meal_type VARCHAR(50),
                food_item VARCHAR(255),
                calories_consumed NUMERIC(8, 2),
                protein_g NUMERIC(8, 2),
                carbs_g NUMERIC(8, 2),
                fat_g NUMERIC(8, 2),
                source VARCHAR(50),
                creation_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (log_date, meal_type, food_item) -- Prevents duplicate entries for the same meal/item on the same day
            );
        """)
        print("Table 'food_log' ensured.")

        # body_measurements table (adjust columns based on your Smart Scale export)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS body_measurements (
                measurement_id BIGSERIAL PRIMARY KEY,
                measurement_date TIMESTAMP WITH TIME ZONE NOT NULL,
                weight_value NUMERIC(7, 2),
                weight_unit VARCHAR(10),
                body_fat_percentage NUMERIC(5, 2),
                bmi_value NUMERIC(5, 2),
                muscle_mass NUMERIC(7, 2),
                source VARCHAR(50),
                creation_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (measurement_date, source) -- Prevents duplicate entries from the same source at the same time
            );
        """)
        print("Table 'body_measurements' ensured.")

        # blood_glucose_meter table (adjust columns based on your glucose meter export)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS blood_glucose_meter (
                glucose_id BIGSERIAL PRIMARY KEY,
                reading_time TIMESTAMP WITH TIME ZONE NOT NULL,
                glucose_value NUMERIC(5, 2),
                glucose_unit VARCHAR(20),
                reading_context VARCHAR(100),
                source VARCHAR(50),
                creation_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (reading_time, source, glucose_value) -- To handle potential exact duplicates
            );
        """)
        print("Table 'blood_glucose_meter' ensured.")

        conn.commit()

    except (Exception, psycopg2.Error) as error:
        print("Error while connecting to PostgreSQL or creating tables:", error)
    finally:
        if conn:
            cur.close()
            conn.close()
            print("PostgreSQL connection closed.")

if __name__ == "__main__":
    create_tables()
