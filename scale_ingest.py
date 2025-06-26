# improved_weight_guru_data.py
"""
Enhanced Weight Guru Data Import Script

This script imports Weight Guru scale data into PostgreSQL with proper error handling,
data validation, and consistency with the overall health data system.
"""

import os
import sys
import getpass
import pandas as pd
import psycopg2
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime
import numpy as np
from scale_ingest import ingest_smart_scale

# Load environment variables
load_dotenv()

# Centralized database configuration - consistent with other scripts
DB_CONFIG = {
    'host': os.getenv("PGHOST", "localhost"),
    'dbname': os.getenv("PGDB", "health_data"),
    'user': os.getenv("PGUSER", getpass.getuser()),
    'password': os.getenv("PGPASS", ""),
    'port': os.getenv("PGPORT", "5432")
}

# Configuration for Weight Guru data import
WEIGHT_GURU_CSV_PATH = Path(os.getenv("WEIGHT_GURU_CSV", 
    r"C:\Users\YourUsername\Downloads\weight_gurus_export.csv"))

# Column mapping - handles variations in Weight Guru export formats
COLUMN_MAPPINGS = {
    # Common variations of column names from different Weight Guru exports
    "Date": "measurement_date",
    "Timestamp": "measurement_date", 
    "DateTime": "measurement_date",
    "Weight": "weight_value",
    "Weight (lb)": "weight_value",
    "Weight (kg)": "weight_value",
    "Unit": "weight_unit",
    "Weight Unit": "weight_unit",
    "Body Fat %": "body_fat_percentage",
    "Body Fat": "body_fat_percentage",
    "BMI": "bmi_value",
    "Muscle lb": "muscle_mass",
    "Muscle Mass": "muscle_mass",
    "Muscle (lb)": "muscle_mass",
    "Muscle (kg)": "muscle_mass",
    "Bone Mass": "bone_mass",
    "Water %": "water_percentage",
    "Water Percentage": "water_percentage", 
    "Metabolic Age": "metabolic_age",
    "Visceral Fat": "visceral_fat_rating",
    "User": "device_user",
    "Device ID": "device_id"
}

def get_db_connection():
    """
    Creates a database connection with proper error handling.
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

def detect_csv_encoding(file_path):
    """
    Detects the encoding of a CSV file to handle international characters.
    Weight Guru
    """