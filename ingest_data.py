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
from ingest_loseit_and_glucose import ingest_loseit_zip, ingest_bloodsugar_csv
from scale_ingest import main as scale_main

# Get default paths from environment
DEFAULT_APPLE_ZIP = os.getenv("APPLE_HEALTH_ZIP_PATH", "")
DEFAULT_LOSEIT_ZIP = os.getenv("LOSEIT_ZIP_PATH", "")
DEFAULT_SCALE_CSV = os.getenv("SCALE_CSV_PATH", "")
DEFAULT_GLUCOSE_CSV = os.getenv("BLOODSUGAR_CSV_PATH", "")

def main():
    parser = argparse.ArgumentParser(
        description="Ingest personal health data into PostgreSQL.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python ingest_data.py --all                    # Ingest all configured sources
  python ingest_data.py --apple --loseit         # Ingest Apple Health and LoseIt
  python ingest_data.py --apple --start 2024-01-01 --end 2024-12-31
  python ingest_data.py --loseit --file /path/to/custom/loseit.zip
        """
    )
    
    # Date filtering options
    parser.add_argument('--start', type=str, help='Start date (YYYY-MM-DD) for filtering data')
    parser.add_argument('--end', type=str, help='End date (YYYY-MM-DD) for filtering data')

    # Data source selection
    parser.add_argument('--apple', action='store_true', help='Ingest Apple Health data')
    parser.add_argument('--loseit', action='store_true', help='Ingest Lose It! data')
    parser.add_argument('--scale', action='store_true', help='Ingest smart scale data')
    parser.add_argument('--glucose', action='store_true', help='Ingest glucose meter data')
    parser.add_argument('--all', action='store_true', help='Ingest all configured sources')
    
    # File path override
    parser.add_argument('--file', type=str, help='Override default file path for the selected source')
    
    args = parser.parse_args()

    if not (args.all or args.apple or args.loseit or args.scale or args.glucose):
        parser.print_help()
        sys.exit(1)

    results = {}

    if args.all or args.apple:
        print("🍎 Starting Apple Health ingestion...")
        apple_health_main()
        results['apple'] = True

    if args.all or args.loseit:
        print("🍽️  Starting LoseIt ingestion...")
        loseit_zip_path = args.file if args.loseit and not (args.apple or args.scale or args.glucose) else DEFAULT_LOSEIT_ZIP
        ingest_loseit_zip(loseit_zip_path, args.start, args.end)
        results['loseit'] = True

    if args.all or args.scale:
        print("⚖️  Starting smart scale ingestion...")
        scale_main()
        results['scale'] = True

    if args.all or args.glucose:
        print("🩸 Starting glucose meter ingestion...")
        glucose_csv_path = args.file if args.glucose and not (args.apple or args.loseit or args.scale) else DEFAULT_GLUCOSE_CSV
        ingest_bloodsugar_csv(glucose_csv_path)
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
    
    if successful == total and total > 0:
        print("🎉 All ingestion processes completed successfully!")
    elif successful > 0:
        print("⚠️  Some ingestion processes completed with errors.")
    else:
        print("❌ All ingestion processes failed.")

    return successful == total and total > 0


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️  Ingestion cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)