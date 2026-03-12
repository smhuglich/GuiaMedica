import sqlite3
import libsql_client
import asyncio
import os

# Turso credentials
TURSO_URL = "https://historiasclinica-smhuglich.aws-us-east-1.turso.io"
TURSO_TOKEN = "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJhIjoicnciLCJleHAiOjE3NzM4NDkwOTYsImlhdCI6MTc3MzI0NDI5NiwiaWQiOiIwMTljZGQ5NC0wODAxLTc4OWQtOWMwNS0xN2MzY2Q1OWZjMDkiLCJyaWQiOiI5ZjAzMDdhYy0wODk3LTQ5YjEtYmQ1OC02MzViMTMxMjQ3MjkifQ.lXR31lF8cKw6imVLcFGbKGAMPcdZSDS0vQwjvXXGQMAvPzAUGHXDVhfTj3qHuPO73z3gaCYdQPMv5SZlUbz8Aw"

async def migrate():
    db_path = 'historiasclinica.db'
    if not os.path.exists(db_path):
        print(f"Error: {db_path} not found.")
        return

    # Connect to local SQLite
    local_conn = sqlite3.connect(db_path)
    local_cursor = local_conn.cursor()

    # Connect to Turso
    client = libsql_client.create_client(TURSO_URL, auth_token=TURSO_TOKEN)

    # 1. Create Tables in Turso
    schema = [
        "DROP TABLE IF EXISTS horarios_atencion;",
        "DROP TABLE IF EXISTS instituciones;",
        "DROP TABLE IF EXISTS profesionales;",
        "DROP TABLE IF EXISTS especialidades;",
        "CREATE TABLE especialidades (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT NOT NULL);",
        "CREATE TABLE instituciones (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT NOT NULL, direccion TEXT, telefono TEXT, especialidad_id INTEGER, FOREIGN KEY (especialidad_id) REFERENCES especialidades(id));",
        "CREATE TABLE profesionales (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT, apellido TEXT);",
        "CREATE TABLE horarios_atencion (id INTEGER PRIMARY KEY AUTOINCREMENT, profesional_id INTEGER, institucion_id INTEGER, dia_semana TEXT, hora_inicio TEXT, hora_fin TEXT, FOREIGN KEY (profesional_id) REFERENCES profesionales(id), FOREIGN KEY (institucion_id) REFERENCES instituciones(id));"
    ]

    print("Setting up schema in Turso...")
    for stmt in schema:
        await client.execute(stmt)

    # 2. Migrate Data in correct order (dependency first)
    tables = ['especialidades', 'profesionales', 'instituciones', 'horarios_atencion']
    for table in tables:
        print(f"Migrating {table}...")
        local_cursor.execute(f"SELECT * FROM {table}")
        rows = local_cursor.fetchall()
        if not rows:
            print(f"No data in {table}")
            continue

        # Get column names
        local_cursor.execute(f"PRAGMA table_info({table})")
        columns = [col[1] for col in local_cursor.fetchall()]
        
        placeholders = ", ".join(["?"] * len(columns))
        insert_sql = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"

        # Insert rows
        for row in rows:
            await client.execute(insert_sql, list(row))
        
        print(f"Migrated {len(rows)} rows to {table}")

    await client.close()
    local_conn.close()
    print("Migration complete!")

if __name__ == "__main__":
    asyncio.run(migrate())
