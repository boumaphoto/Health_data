# create_health_database.py (updated for Lose It + bloodsugar)
import os
import sys
import getpass
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

DB_CONFIG = {
    'host': os.getenv("PGHOST", "localhost"),
    'dbname': os.getenv("PGDB", "health_data"),
    'user': os.getenv("PGUSER", getpass.getuser()),
    'password': os.getenv("PGPASS", ""),
    'port': os.getenv("PGPORT", "5432")
}

def get_db_connection():
    try:
        return psycopg2.connect(**DB_CONFIG)
    except Exception as e:
        print(f"Database connection failed: {e}")
        return None

def create_tables():
    conn = get_db_connection()
    if not conn:
        return False

    try:
        cur = conn.cursor()

        # --- HEALTH RECORDS (Consolidated from Apple Health) ---
        cur.execute("""
            CREATE TABLE IF NOT EXISTS health_records (
                id SERIAL PRIMARY KEY,
                type VARCHAR(255) NOT NULL,
                source_name VARCHAR(255) NOT NULL,
                source_version VARCHAR(255),
                device VARCHAR(255),
                unit VARCHAR(50),
                creation_date TIMESTAMP WITH TIME ZONE,
                start_date TIMESTAMP WITH TIME ZONE NOT NULL,
                end_date TIMESTAMP WITH TIME ZONE NOT NULL,
                value TEXT,
                UNIQUE (type, start_date, end_date, value)
            );
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS health_category_records (
                id SERIAL PRIMARY KEY,
                type VARCHAR(255) NOT NULL,
                source_name VARCHAR(255) NOT NULL,
                source_version VARCHAR(255),
                device VARCHAR(255),
                unit VARCHAR(50),
                creation_date TIMESTAMP WITH TIME ZONE,
                start_date TIMESTAMP WITH TIME ZONE NOT NULL,
                end_date TIMESTAMP WITH TIME ZONE NOT NULL,
                value TEXT,
                UNIQUE (type, start_date, end_date, value)
            );
        """)

        # --- WORKOUTS ---
        cur.execute("""
            CREATE TABLE IF NOT EXISTS workouts (
                id SERIAL PRIMARY KEY,
                activity_name VARCHAR(255) NOT NULL,
                duration FLOAT,
                duration_unit VARCHAR(50),
                total_distance FLOAT,
                total_distance_unit VARCHAR(50),
                total_energy_burned FLOAT,
                total_energy_burned_unit VARCHAR(50),
                source_name VARCHAR(255) NOT NULL,
                source_version VARCHAR(255),
                device VARCHAR(255),
                creation_date TIMESTAMP WITH TIME ZONE,
                start_date TIMESTAMP WITH TIME ZONE NOT NULL,
                end_date TIMESTAMP WITH TIME ZONE NOT NULL,
                UNIQUE (activity_name, start_date, end_date)
            );
        """)

        # --- FOOD LOG (from LoseIt) ---
        cur.execute("""
            CREATE TABLE IF NOT EXISTS food_log (
                id SERIAL PRIMARY KEY,
                log_date DATE NOT NULL,
                name TEXT,
                meal TEXT,
                calories NUMERIC(6,2),
                fat_g NUMERIC(6,2),
                protein_g NUMERIC(6,2),
                carbs_g NUMERIC(6,2),
                sugars_g NUMERIC(6,2),
                fiber_g NUMERIC(6,2),
                sodium_mg NUMERIC(6,2),
                source TEXT DEFAULT 'LoseIt',
                UNIQUE (log_date, name, meal)
            );
        """)

        # --- BODY MEASUREMENTS (from smart scale) ---
        cur.execute("""
            CREATE TABLE IF NOT EXISTS body_measurements (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
                weight_kg FLOAT,
                body_fat_percentage FLOAT,
                muscle_mass_kg FLOAT,
                bmi FLOAT,
                metabolic_age INTEGER,
                visceral_fat INTEGER,
                water_percentage FLOAT,
                device_id VARCHAR(255),
                source VARCHAR(255),
                UNIQUE(timestamp, device_id)
            );
        """)

        # --- BLOOD GLUCOSE ---
        cur.execute("""
            CREATE TABLE IF NOT EXISTS blood_glucose (
                id SERIAL PRIMARY KEY,
                reading_time TIMESTAMP WITH TIME ZONE NOT NULL,
                glucose_value NUMERIC(6,2) NOT NULL,
                glucose_unit VARCHAR(20) DEFAULT 'mg/dL',
                reading_context VARCHAR(100),
                meal_relation VARCHAR(50),
                feeling_tag VARCHAR(100),
                note TEXT,
                source VARCHAR(50) DEFAULT 'manual',
                creation_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (reading_time, glucose_value)
            );
        """)

        conn.commit()
        print("✅ All tables created or ensured.")
        return True

    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        conn.rollback()
        return False
    finally:
        if conn:
            cur.close()
            conn.close()

if __name__ == "__main__":
    create_tables()
