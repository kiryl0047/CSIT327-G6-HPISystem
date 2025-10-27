# test_supabase_conn.py
import os
import psycopg2
from urllib.parse import urlparse

db_url = os.getenv('DATABASE_URL')
if not db_url:
    print("DATABASE_URL not set in environment.")
    raise SystemExit(1)

result = urlparse(db_url)
dbname = result.path.lstrip('/')
user = result.username
password = result.password
host = result.hostname
port = result.port or 5432

print("Trying to connect to", host, port, dbname, user)
try:
    conn = psycopg2.connect(
        dbname=dbname,
        user=user,
        password=password,
        host=host,
        port=port,
        sslmode='require'
    )
    print("Connected OK, status:", conn.status)
    conn.close()
except Exception as e:
    print("Connection FAILED:", type(e).__name__, e)