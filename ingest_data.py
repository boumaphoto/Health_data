import argparse
from pathlib import Path
from apple_ingest import ingest_apple_health
from loseit_ingest import ingest_loseit
from scale_ingest import ingest_smart_scale

def main():
    parser = argparse.ArgumentParser(description="Ingest personal health data into PostgreSQL.")
    parser.add_argument('--apple', action='store_true', help='Ingest Apple Health data')
    parser.add_argument('--loseit', action='store_true', help='Ingest Lose It! data')
    parser.add_argument('--scale', action='store_true', help='Ingest smart scale data')
    parser.add_argument('--file', type=str, help='Optional file path override')
    parser.add_argument('--all', action='store_true', help='Ingest all sources')

    args = parser.parse_args()

    if args.all or args.apple:
        ingest_apple_health()
    if args.all or args.loseit:
        ingest_loseit(csv_path=args.file)
    if args.all or args.scale:
        ingest_smart_scale(csv_path=args.file)

if __name__ == "__main__":
    main()
