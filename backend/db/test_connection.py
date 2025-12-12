"""
Test database connection for different scenarios.
"""
import psycopg2
import os

# Test configurations
configs = [
    {
        "name": "Localhost",
        "host": "localhost",
        "port": "5432",
        "user": "postgres",
        "password": "agent123",
        "database": "postgres"
    },
    {
        "name": "Docker Container Name",
        "host": "postgres-db",
        "port": "5432",
        "user": "postgres",
        "password": "agent123",
        "database": "postgres"
    },
    {
        "name": "127.0.0.1",
        "host": "127.0.0.1",
        "port": "5432",
        "user": "postgres",
        "password": "agent123",
        "database": "postgres"
    }
]

print("Testing database connections...\n")

for config in configs:
    try:
        print(f"Testing: {config['name']} ({config['host']}:{config['port']})...")
        conn = psycopg2.connect(
            host=config["host"],
            port=config["port"],
            user=config["user"],
            password=config["password"],
            database=config["database"],
            connect_timeout=3
        )
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"  ✅ SUCCESS! Version: {version[:50]}...\n")
        cursor.close()
        conn.close()
        break
    except Exception as e:
        print(f"  ❌ FAILED: {str(e)[:100]}...\n")

print("\nTo fix connection issues:")
print("1. Verify postgres container is running: docker ps")
print("2. Check port mapping: docker port postgres-db")
print("3. If port not exposed, restart with: docker run -d --name postgres-db --network agent-net -p 5432:5432 -e POSTGRES_PASSWORD=agent123 postgres")
