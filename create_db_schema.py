import argparse
import os, getpass
from dotenv import load_dotenv
import psycopg2

# Load .env values
load_dotenv()

DB = dict(
    host=os.getenv("PGHOST", "localhost"),
    dbname=os.getenv("PGDB", "health_data"),
    user=os.getenv("PGUSER", getpass.getuser()),
    password=os.getenv("PGPASS", ""),
)

def create_tables():
    print("Creating tables...")
    conn = None
    try:
        conn = psycopg2.connect(**DB)
        cur = conn.cursor()

        # Example table creation (shortened for clarity)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS example (
                id SERIAL PRIMARY KEY,
                name TEXT
            );
        """)
        print("✔️  Tables created.")
        conn.commit()

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if conn:
            cur.close()
            conn.close()

def drop_tables():
    print("Dropping tables... (add logic here)")

def main():
    parser = argparse.ArgumentParser(description="Manage health database schema.")
    parser.add_argument("--create", action="store_true", help="Create tables")
    parser.add_argument("--drop", action="store_true", help="Drop tables")

    args = parser.parse_args()

    if args.create:
        create_tables()
    elif args.drop:
        drop_tables()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
