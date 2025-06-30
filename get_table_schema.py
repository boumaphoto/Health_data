import psycopg2
import os
import sys
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('PGHOST', 'localhost'),
    'dbname': os.getenv('PGDB', 'health_data'),
    'user': os.getenv('PGUSER', os.getlogin()),
    'password': os.getenv('PGPASS', ''),
    'port': os.getenv('PGPORT', '5432')
}

def get_table_schema(table_name):
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table_name}'")
        columns = cur.fetchall()
        print(f'Columns for {table_name}:')
        for c in columns:
            print(f'{c[0]}: {c[1]}')
        cur.close()
        conn.close()
    except psycopg2.OperationalError as e:
        print(f'Database connection error: {e}')
        sys.exit(1)

if __name__ == '__main__':
    if len(sys.argv) > 1:
        get_table_schema(sys.argv[1])
    else:
        print("Usage: python get_table_schema.py <table_name>")
        sys.exit(1)
