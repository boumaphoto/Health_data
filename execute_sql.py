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

def execute_sql(sql_query):
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute(sql_query)
        conn.commit()
        print("SQL executed successfully.")
        if cur.rowcount > 0:
            print(f"{cur.rowcount} rows affected.")
        cur.close()
        conn.close()
    except psycopg2.OperationalError as e:
        print(f'Database connection error: {e}')
        sys.exit(1)
    except Exception as e:
        print(f'SQL execution error: {e}')
        sys.exit(1)

if __name__ == '__main__':
    if len(sys.argv) > 1:
        # Read SQL from a file specified as the first argument
        sql_file_path = sys.argv[1]
        with open(sql_file_path, 'r') as f:
            sql_query = f.read()
        execute_sql(sql_query)
    else:
        print("Usage: python execute_sql.py <sql_file_path>")
        sys.exit(1)
