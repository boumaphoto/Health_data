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
# from scale_ingest import ingest_smart_scale  # Uncomment when you create this
# from glucose_ingest import ingest_glucose    # Uncomment when you create this

# Get default paths from environment
DEFAULT_APPLE_ZIP = os.getenv("APPLE_HEALTH_ZIP_PATH", "")
DEFAULT_LOSEIT_ZIP = os.getenv("LOSEIT_ZIP_PATH", "")
DEFAULT_SCALE_CSV = os.getenv("SCALE_CSV_PATH", "")
DEFAULT_GLUCOSE_CSV = os.getenv("GLUCOSE_CSV_PATH", "")


def ingest_apple_health(start_date=None, end_date=None, zip_path=None):
    """Wrapper for Apple Health ingestion."""
    if zip_path is None:
        zip_path = DEFAULT_APPLE_ZIP
    
    if not zip_path:
        print("No Apple Health ZIP path provided. Set APPLE_HEALTH_ZIP_PATH in .env or use --file parameter.")
        return False
    
    zip_file = Path(zip_path)
    if not zip_file.exists():
        print(f"Apple Health ZIP file not found: {zip_path}")
        return False
    
    try:
        print("🍎 Starting Apple Health ingestion...")
        apple_health_main(zip_file, start_date, end_date)
        return True
    except Exception as e:
        print(f"Error ingesting Apple Health data: {e}")
        return False


def ingest_smart_scale(csv_path=None):
    """Placeholder for smart scale ingestion - implement when you create the script."""
    if csv_path is None:
        csv_path = DEFAULT_SCALE_CSV
    
    if not csv_path:
        print("No smart scale CSV path provided. Set SCALE_CSV_PATH in .env or use --file parameter.")
        return False
    
    print("⚖️  Smart scale ingestion not yet implemented.")
    print(f"Would process: {csv_path}")
    # TODO: Implement scale_ingest.ingest_smart_scale(csv_path)
    return False


def ingest_glucose(csv_path=None):
    """Placeholder for glucose meter ingestion - implement when you create the script."""
    if csv_path is None:
        csv_path = DEFAULT_GLUCOSE_CSV
    
    if not csv_path:
        print("No glucose CSV path provided. Set GLUCOSE_CSV_PATH in .env or use --file parameter.")
        return False
    
    print("🩸 Glucose meter ingestion not yet implemented.")
    print(f"Would process: {csv_path}")
    # TODO: Implement glucose_ingest.ingest_glucose(csv_path)
    return False


def main():
    parser = argparse.ArgumentParser(
        description="Ingest personal health data into PostgreSQL.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python ingest_data.py --all                    # Ingest all configured sources
  python ingest_data.py --apple --loseit         # Ingest Apple Health and LoseIt
  python ingest_data.py --apple --start 2024-01-01 --end 2024-12-31
  python ingest_data.py --loseit --file /path/to/custom/loseit.csv
        """
    )
    
    # Date filtering options
    parser.add_argument('--start', type=str, help='Start date (YYYY-MM-DD) for Apple Health data')
    parser.add_argument('--end', type=str, help='End date (YYYY-MM-DD) for Apple Health data')

    # Data source selection
    parser.add_argument('--apple', action='store_true', help='Ingest Apple Health data')
    parser.add_argument('--loseit', action='store_true', help='Ingest Lose It! data')
    parser.add_argument('--scale', action='store_true', help='Ingest smart scale data')
    parser.add_argument('--glucose', action='store_true', help='Ingest glucose meter data')
    parser.add_argument('--all', action='store_true', help='Ingest all configured sources')
    
    # File path override
    parser.add_argument('--file', type=str, help='Override default file path for the selected source')
    
    # Verbose output
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output')

    args = parser.parse_args()

    # If no sources specified, show help
    if not (args.all or args.apple or args.loseit or args.scale or args.glucose):
        parser.print_help()
        sys.exit(1)

    # Track success/failure
    results = {}

    # Validate date format if provided
    if args.start:
        try:
            from datetime import datetime
            datetime.strptime(args.start, '%Y-%m-%d')
        except ValueError:
            print("Error: Start date must be in YYYY-MM-DD format")
            sys.exit(1)
    
    if args.end:
        try:
            from datetime import datetime
            datetime.strptime(args.end, '%Y-%m-%d')
        except ValueError:
            print("Error: End date must be in YYYY-MM-DD format")
            sys.exit(1)

    print("🚀 Starting health data ingestion...")
    if args.verbose:
        print(f"Date range: {args.start or 'all'} to {args.end or 'all'}")
        print(f"Custom file: {args.file or 'using defaults'}")

    # Apple Health ingestion
    if args.all or args.apple:
        file_path = args.file if args.apple and not (args.loseit or args.scale or args.glucose) else None
        results['apple'] = ingest_apple_health(
            start_date=args.start, 
            end_date=args.end, 
            zip_path=file_path
        )

    # LoseIt ingestion
    if args.all or args.loseit:
        file_path = args.file if args.loseit and not (args.apple or args.scale or args.glucose) else None
        try:
            print("🍽️  Starting LoseIt ingestion...")
            ath=file_path, start_date=args.start, end_date=args.end)ingest_loseit(ZIP_path=file_path, start_date=args.start, end_date=args.end)

            results['loseit'] = True
        except Exception as e:
            print(f"Error ingesting LoseIt data: {e}")
            results['loseit'] = False

    # Smart scale ingestion
    if args.all or args.scale:
        file_path = args.file if args.scale and not (args.apple or args.loseit or args.glucose) else None
        results['scale'] = ingest_smart_scale(csv_path=file_path)

    # Glucose meter ingestion
    if args.all or args.glucose:
        file_path = args.file if args.glucose and not (args.apple or args.loseit or args.scale) else None
        results['glucose'] = ingest_glucose(csv_path=file_path)

    # Summary
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