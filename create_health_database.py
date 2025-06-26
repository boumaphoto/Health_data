# v.2 improved_create_health_database.py
import os
import sys
import getpass
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file
load_dotenv()

# Centralized database configuration
DB_CONFIG = {
    'host': os.getenv("PGHOST", "localhost"),
    'dbname': os.getenv("PGDB", "health_data"),
    'user': os.getenv("PGUSER", getpass.getuser()),
    'password': os.getenv("PGPASS", ""),
    'port': os.getenv("PGPORT", "5432")
}

def get_db_connection():
    """
    Creates and returns a database connection using centralized configuration.
    This function handles connection errors gracefully and provides helpful error messages.
    """
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except psycopg2.OperationalError as e:
        print(f"❌ Database connection failed: {e}")
        print("Please check your database configuration in the .env file")
        return None
    except Exception as e:
        print(f"❌ Unexpected error connecting to database: {e}")
        return None

def create_tables():
    """
    Creates all necessary tables for the health data system.
    Each table includes proper indexing for common query patterns.
    """
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cur = conn.cursor()
        
        # Health records table - improved with composite primary key
        print("Creating health_records table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS health_records (
                record_id BIGSERIAL PRIMARY KEY,
                type VARCHAR(100) NOT NULL,
                start_date TIMESTAMP WITH TIME ZONE NOT NULL,
                end_date TIMESTAMP WITH TIME ZONE NOT NULL,
                value NUMERIC(12, 6),  -- Increased precision for more accurate measurements
                unit VARCHAR(50),
                source_name VARCHAR(100),
                creation_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                -- Composite unique constraint prevents exact duplicates
                CONSTRAINT unique_health_record UNIQUE (type, start_date, end_date, value, source_name)
            );
        """)
        
        # Add indexes for common query patterns
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_health_records_type_date 
            ON health_records(type, start_date);
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_health_records_source_date 
            ON health_records(source_name, start_date);
        """)
        
        # Health category records table
        print("Creating health_category_records table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS health_category_records (
                record_id BIGSERIAL PRIMARY KEY,
                type VARCHAR(100) NOT NULL,
                start_date TIMESTAMP WITH TIME ZONE NOT NULL,
                end_date TIMESTAMP WITH TIME ZONE NOT NULL,
                value VARCHAR(100),  -- Increased length for category values
                source_name VARCHAR(100),
                creation_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT unique_category_record UNIQUE (type, start_date, end_date, value, source_name)
            );
        """)
        
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_category_records_type_date 
            ON health_category_records(type, start_date);
        """)
        
        # Workouts table - enhanced with more flexibility
        print("Creating workouts table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS workouts (
                workout_id BIGSERIAL PRIMARY KEY,
                activity_type VARCHAR(100) NOT NULL,
                start_date TIMESTAMP WITH TIME ZONE NOT NULL,
                end_date TIMESTAMP WITH TIME ZONE NOT NULL,
                duration_seconds NUMERIC(10, 2),
                total_distance NUMERIC(12, 4),  -- Increased precision
                distance_unit VARCHAR(50),
                total_energy_burned NUMERIC(10, 2),
                energy_unit VARCHAR(50),
                source_name VARCHAR(100),
                -- Additional useful workout metrics
                average_heart_rate NUMERIC(5, 2),
                max_heart_rate NUMERIC(5, 2),
                notes TEXT,
                creation_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT unique_workout UNIQUE (activity_type, start_date, end_date, source_name)
            );
        """)
        
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_workouts_activity_date 
            ON workouts(activity_type, start_date);
        """)
        
        # Food log table - improved structure
        print("Creating food_log table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS food_log (
                log_id BIGSERIAL PRIMARY KEY,
                log_date DATE NOT NULL,
                log_time TIME,  -- Separate time field for more flexibility
                meal_type VARCHAR(50),
                food_item VARCHAR(500),  -- Increased length for detailed food names
                brand VARCHAR(200),
                serving_size VARCHAR(100),
                calories_consumed NUMERIC(8, 2),
                protein_g NUMERIC(8, 2),
                carbs_g NUMERIC(8, 2),
                fat_g NUMERIC(8, 2),
                fiber_g NUMERIC(8, 2),
                sugar_g NUMERIC(8, 2),
                sodium_mg NUMERIC(8, 2),
                source VARCHAR(50) DEFAULT 'LoseIt',
                creation_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                -- Prevent duplicate entries but allow multiple servings of same food
                CONSTRAINT unique_food_entry UNIQUE (log_date, log_time, meal_type, food_item, brand, serving_size)
            );
        """)
        
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_food_log_date 
            ON food_log(log_date);
        """)
        
        # Body measurements table - enhanced with more metrics
        print("Creating body_measurements table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS body_measurements (
                measurement_id BIGSERIAL PRIMARY KEY,
                measurement_date TIMESTAMP WITH TIME ZONE NOT NULL,
                weight_value NUMERIC(7, 2),
                weight_unit VARCHAR(10) DEFAULT 'lb',
                body_fat_percentage NUMERIC(5, 2),
                bmi_value NUMERIC(5, 2),
                muscle_mass NUMERIC(7, 2),
                muscle_mass_unit VARCHAR(10),
                bone_mass NUMERIC(7, 2),
                water_percentage NUMERIC(5, 2),
                metabolic_age INTEGER,
                visceral_fat_rating NUMERIC(4, 1),
                source VARCHAR(50) DEFAULT 'WeightGurus',
                device_id VARCHAR(100),  -- Track which specific device made the measurement
                creation_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT unique_body_measurement UNIQUE (measurement_date, source, device_id)
            );
        """)
        
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_body_measurements_date 
            ON body_measurements(measurement_date);
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_body_measurements_source_date 
            ON body_measurements(source, measurement_date);
        """)
        
        # Blood glucose table - improved with context tracking
        print("Creating blood_glucose_meter table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS blood_glucose_meter (
                glucose_id BIGSERIAL PRIMARY KEY,
                reading_time TIMESTAMP WITH TIME ZONE NOT NULL,
                glucose_value NUMERIC(6, 2),  -- Increased precision
                glucose_unit VARCHAR(20) DEFAULT 'mg/dL',
                reading_context VARCHAR(100),  -- Before meal, after meal, bedtime, etc.
                meal_relation VARCHAR(50),     -- Which meal this relates to
                notes TEXT,
                source VARCHAR(50),
                device_id VARCHAR(100),
                creation_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT unique_glucose_reading UNIQUE (reading_time, source, device_id)
            );
        """)
        
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_glucose_reading_time 
            ON blood_glucose_meter(reading_time);
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_glucose_context 
            ON blood_glucose_meter(reading_context, reading_time);
        """)
        
        # Create a summary view for easy daily aggregations
        print("Creating daily_summary view...")
        cur.execute("""
            CREATE OR REPLACE VIEW daily_health_summary AS
            SELECT 
                date_trunc('day', measurement_date)::date as summary_date,
                AVG(weight_value) as avg_weight,
                AVG(body_fat_percentage) as avg_body_fat,
                AVG(bmi_value) as avg_bmi,
                COUNT(*) as measurement_count
            FROM body_measurements 
            WHERE weight_value IS NOT NULL
            GROUP BY date_trunc('day', measurement_date)
            ORDER BY summary_date DESC;
        """)
        
        conn.commit()
        print("✅ All tables and indexes created successfully!")
        return True
        
    except psycopg2.Error as e:
        print(f"❌ Database error while creating tables: {e}")
        conn.rollback()
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    finally:
        if conn:
            cur.close()
            conn.close()

def drop_tables():
    """
    Drops all health data tables. Use with caution!
    """
    conn = get_db_connection()
    if not conn:
        return False
    
    # Confirm before dropping
    confirm = input("⚠️  This will delete ALL health data. Type 'DELETE ALL DATA' to confirm: ")
    if confirm != "DELETE ALL DATA":
        print("Operation cancelled.")
        return False
    
    try:
        cur = conn.cursor()
        
        # Drop tables in reverse order of dependencies
        tables_to_drop = [
            'daily_health_summary',  # This is a view
            'blood_glucose_meter',
            'body_measurements', 
            'food_log',
            'workouts',
            'health_category_records',
            'health_records'
        ]
        
        for table in tables_to_drop:
            print(f"Dropping {table}...")
            cur.execute(f"DROP TABLE IF EXISTS {table} CASCADE;")
        
        conn.commit()
        print("✅ All tables dropped successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error dropping tables: {e}")
        return False
    finally:
        if conn:
            cur.close()
            conn.close()

def test_connection():
    """
    Tests the database connection and displays configuration info.
    """
    print("Testing database connection...")
    print(f"Host: {DB_CONFIG['host']}")
    print(f"Database: {DB_CONFIG['dbname']}")
    print(f"User: {DB_CONFIG['user']}")
    print(f"Port: {DB_CONFIG['port']}")
    
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("SELECT version();")
            version = cur.fetchone()
            print(f"✅ Connected to PostgreSQL: {version[0]}")
            return True
        except Exception as e:
            print(f"❌ Error testing connection: {e}")
            return False
        finally:
            cur.close()
            conn.close()
    return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Manage health database schema")
    parser.add_argument("--create", action="store_true", help="Create all tables")
    parser.add_argument("--drop", action="store_true", help="Drop all tables")
    parser.add_argument("--test", action="store_true", help="Test database connection")
    
    args = parser.parse_args()
    
    if args.test:
        test_connection()
    elif args.create:
        create_tables()
    elif args.drop:
        drop_tables()
    else:
        # Interactive mode
        print("Health Database Schema Manager")
        print("1. Test connection")
        print("2. Create tables")
        print("3. Drop tables")
        choice = input("Select option (1-3): ")
        
        if choice == "1":
            test_connection()
        elif choice == "2":
            create_tables()
        elif choice == "3":
            drop_tables()
        else:
            print("Invalid choice")