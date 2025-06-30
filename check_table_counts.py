import os
import psycopg2
import csv
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'host': os.getenv("PGHOST", "localhost"),
    'dbname': os.getenv("PGDB", "health_data"),
    'user': os.getenv("PGUSER", os.getlogin()),
    'password': os.getenv("PGPASS", ""),
    'port': os.getenv("PGPORT", "5432")
}

tables = [
    'health_records',
    'health_category_records',
    'workouts',
    'food_log',
    'body_measurements',
    'blood_glucose_manual'
]

results = []

try:
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    print("\n📊 Table diagnostics:")
    for table in tables:
        try:
            cur.execute(f"SELECT COUNT(*) FROM {table};")
            count = cur.fetchone()[0]

            cur.execute(f"SELECT * FROM {table} LIMIT 1;")
            sample = cur.fetchone()

            cur.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table}';")
            columns = [row[0] for row in cur.fetchall()]

            min_id, max_id = None, None
            for col in columns:
                if 'id' in col:
                    cur.execute(f"SELECT MIN({col}), MAX({col}) FROM {table};")
                    min_id, max_id = cur.fetchone()
                    break

            print(f"\nTable: {table}")
            print(f"  Row count: {count}")
            print(f"  Columns: {columns}")
            print(f"  Sample row: {sample}")
            print(f"  Min ID: {min_id}, Max ID: {max_id}")

            results.append({
                'table': table,
                'count': count,
                'columns': '|'.join(columns),
                'sample_row': str(sample),
                'min_id': min_id,
                'max_id': max_id
            })
        except Exception as e:
            print(f"❌ ERROR - {table}: {e}")
    cur.close()
    conn.close()

    # Export to CSV
    with open('table_diagnostics.csv', 'w', newline='') as csvfile:
        fieldnames = ['table', 'count', 'columns', 'sample_row', 'min_id', 'max_id']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in results:
            writer.writerow(row)
    print("\n✅ Diagnostics written to table_diagnostics.csv")

except Exception as e:
    print(f"❌ Database connection failed: {e}")
