import asyncio
import libsql_client
import psycopg

# --- Credentials ---
TURSO_URL = "https://historiasclinica-smhuglich.aws-us-east-1.turso.io"
TURSO_TOKEN = "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJhIjoicnciLCJleHAiOjE3NzM4NDkwOTYsImlhdCI6MTc3MzI0NDI5NiwiaWQiOiIwMTljZGQ5NC0wODAxLTc4OWQtOWMwNS0xN2MzY2Q1OWZjMDkiLCJyaWQiOiI5ZjAzMDdhYy0wODk3LTQ5YjEtYmQ1OC02MzViMTMxMjQ3MjkifQ.lXR31lF8cKw6imVLcFGbKGAMPcdZSDS0vQwjvXXGQMAvPzAUGHXDVhfTj3qHuPO73z3gaCYdQPMv5SZlUbz8Aw"

NEON_CONN = "postgresql://neondb_owner:npg_5lWQGfRMTS4m@ep-rough-firefly-ad4grf6i-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require"

async def migrate():
    print("Connecting to Turso and Neon...")
    turso = libsql_client.create_client(TURSO_URL, auth_token=TURSO_TOKEN)
    neon = await psycopg.AsyncConnection.connect(NEON_CONN)
    
    try:
        async with neon.cursor() as cur:
            # 1. Especialidades
            print("Migrating especialidades...")
            rs = await turso.execute("SELECT id, nombre FROM especialidades")
            for row in rs.rows:
                await cur.execute(
                    "INSERT INTO especialidades (id, nombre) VALUES (%s, %s) ON CONFLICT (id) DO UPDATE SET nombre = EXCLUDED.nombre",
                    (row[0], row[1])
                )
            
            # 2. Instituciones
            print("Migrating instituciones...")
            rs = await turso.execute("SELECT id, nombre, direccion, telefono, lat, lng FROM instituciones")
            for row in rs.rows:
                await cur.execute(
                    "INSERT INTO instituciones (id, nombre, direccion, telefono, lat, lng) VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT (id) DO UPDATE SET nombre = EXCLUDED.nombre, direccion = EXCLUDED.direccion, telefono = EXCLUDED.telefono, lat = EXCLUDED.lat, lng = EXCLUDED.lng",
                    (row[0], row[1], row[2], row[3], row[4], row[5])
                )
            
            # 3. Profesionales
            print("Migrating profesionales...")
            rs = await turso.execute("SELECT id, nombre, apellido, matricula, telefono FROM profesionales")
            for row in rs.rows:
                await cur.execute(
                    "INSERT INTO profesionales (id, nombre, apellido, matricula, telefono) VALUES (%s, %s, %s, %s, %s) ON CONFLICT (id) DO UPDATE SET nombre = EXCLUDED.nombre, apellido = EXCLUDED.apellido, matricula = EXCLUDED.matricula, telefono = EXCLUDED.telefono",
                    (row[0], row[1], row[2], row[3], row[4])
                )
            
            # 4. institucion_especialidad
            print("Migrating institucion_especialidad...")
            rs = await turso.execute("SELECT institucion_id, especialidad_id FROM institucion_especialidad")
            for row in rs.rows:
                await cur.execute(
                    "INSERT INTO institucion_especialidad (institucion_id, especialidad_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                    (row[0], row[1])
                )
            
            # 5. horarios_atencion
            print("Migrating horarios_atencion...")
            rs = await turso.execute("SELECT id, profesional_id, institucion_id, dia_num, hora_inicio, hora_fin FROM horarios_atencion")
            for row in rs.rows:
                await cur.execute(
                    "INSERT INTO horarios_atencion (id, profesional_id, institucion_id, dia_num, hora_inicio, hora_fin) VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT (id) DO UPDATE SET profesional_id = EXCLUDED.profesional_id, institucion_id = EXCLUDED.institucion_id, dia_num = EXCLUDED.dia_num, hora_inicio = EXCLUDED.hora_inicio, hora_fin = EXCLUDED.hora_fin",
                    (row[0], row[1], row[2], row[3], row[4], row[5])
                )
            
            # Reset sequences for serial columns
            print("Resetting sequences...")
            await cur.execute("SELECT setval(pg_get_serial_sequence('especialidades', 'id'), coalesce(max(id), 0) + 1, false) FROM especialidades")
            await cur.execute("SELECT setval(pg_get_serial_sequence('instituciones', 'id'), coalesce(max(id), 0) + 1, false) FROM instituciones")
            await cur.execute("SELECT setval(pg_get_serial_sequence('profesionales', 'id'), coalesce(max(id), 0) + 1, false) FROM profesionales")
            await cur.execute("SELECT setval(pg_get_serial_sequence('horarios_atencion', 'id'), coalesce(max(id), 0) + 1, false) FROM horarios_atencion")
            
            await neon.commit()
            print("Migration completed successfully!")
            
    finally:
        await turso.close()
        await neon.close()

if __name__ == "__main__":
    asyncio.run(migrate())
