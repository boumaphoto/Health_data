# ingest_data.py

import argparse
import sys
from pathlib import Path
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Import your ingestion modules
from convert_apple_health import main as apple_health_main
from ingest_lose_it import ingest_loseit
from ingest_glucose_data import ingest_glucose_data
# from scale_ingest import main as scale_main

# Get default paths from environment
DEFAULT_APPLE_ZIP = os.getenv("APPLE_HEALTH_ZIP_PATH", "")
DEFAULT_LOSEIT_ZIP = os.getenv("LOSEIT_ZIP_PATH", "")
DEFAULT_GLUCOSE_CSV = os.getenv("BLOODSUGAR_CSV_PATH", "")

def main():
    parser = argparse.ArgumentParser(description="Ingest personal health data into PostgreSQL.")
    parser.add_argument('--apple', action='store_true', help='Ingest Apple Health data')
    parser.add_argument('--loseit', action='store_true', help='Ingest Lose It! data')
    parser.add_argument('--glucose', action='store_true', help='Ingest glucose meter data')
    parser.add_argument('--all', action='store_true', help='Ingest all configured sources')
    parser.add_argument('--file', type=str, help='Override default file path for the selected source')

    args = parser.parse_args()

    results = {}

    if args.all or args.apple:
        print("🍎 Starting Apple Health ingestion...")
        apple_health_main()
        results['apple'] = True

    if args.all or args.loseit:
        print("🍽️  Starting LoseIt ingestion...")
        ingest_loseit()
        results['loseit'] = True

    if args.all or args.glucose:
        print("🩸 Starting glucose meter ingestion...")
        ingest_glucose_data()
        results['glucose'] = True

    print("\n" + "="*50)
    print("📊 INGESTION SUMMARY")
    print("="*50)

    for source, success in results.items():
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"{source.capitalize():12} {status}")

    successful = sum(1 for success in results.values() if success)
    total = len(results)
    print(f"\nCompleted: {successful}/{total} sources")

if __name__ == "__main__":
    main()
