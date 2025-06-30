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

try:
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
    tables = cur.fetchall()
    print('Tables:')
    for t in tables:
        print(t[0])
    cur.close()
    conn.close()
except psycopg2.OperationalError as e:
    print(f'Database connection error: {e}')
    sys.exit(1)
