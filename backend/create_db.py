import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv
from urllib.parse import urlparse, unquote

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/haire_db")
parsed = urlparse(DATABASE_URL)

dbname = parsed.path[1:]
user = parsed.username
password = unquote(parsed.password) if parsed.password else None
host = parsed.hostname
port = parsed.port

# Connect to the default 'postgres' database to create a new database
try:
    conn = psycopg2.connect(dbname='postgres', user=user, password=password, host=host, port=port)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()
    
    # Check if database exists
    cursor.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{dbname}'")
    exists = cursor.fetchone()
    if not exists:
        cursor.execute(f'CREATE DATABASE {dbname}')
        print(f"Database {dbname} created successfully.")
    else:
        print(f"Database {dbname} already exists.")
        
    cursor.close()
    conn.close()
except Exception as e:
    print(f"Error creating database: {e}")
