import psycopg2

try:
    # Connect to Supabase pooler
    conn = psycopg2.connect(
        dbname="postgres",  # your database name
        user="postgres.mdrdopacxswruyhmpgad",  # your Supabase user
        password="TranCIT0987612345",  # replace with your password
        host="aws-1-us-east-2.pooler.supabase.com",  # pooler host
        port="6543",  # pooler port
        sslmode="require"  # Supabase requires SSL
    )

    cur = conn.cursor()
    cur.execute("SELECT version();")  # simple test query
    version = cur.fetchone()
    print("Connection successful! PostgreSQL version:", version)

    cur.close()
    conn.close()

except Exception as e:
    print("Connection failed:", e)
