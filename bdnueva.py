import asyncio
import libsql_client

DB_URL = "https://historiasclinica-smhuglich.aws-us-east-1.turso.io"
DB_TOKEN = "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJhIjoicnciLCJleHAiOjE3NzM4NDkwOTYsImlhdCI6MTc3MzI0NDI5NiwiaWQiOiIwMTljZGQ5NC0wODAxLTc4OWQtOWMwNS0xN2MzY2Q1OWZjMDkiLCJyaWQiOiI5ZjAzMDdhYy0wODk3LTQ5YjEtYmQ1OC02MzViMTMxMjQ3MjkifQ.lXR31lF8cKw6imVLcFGbKGAMPcdZSDS0vQwjvXXGQMAvPzAUGHXDVhfTj3qHuPO73z3gaCYdQPMv5SZlUbz8Aw"

async def migrate_database():

    client = libsql_client.create_client(
        DB_URL,
        auth_token=DB_TOKEN
    )

    print("Conectado a Turso")

    # --------------------------------
    # 1 CREAR INDICES PARA PERFORMANCE
    # --------------------------------

    print("Creando índices...")

    await client.execute("""
    CREATE INDEX IF NOT EXISTS idx_instituciones_especialidad
    ON instituciones(especialidad_id);
    """)

    await client.execute("""
    CREATE INDEX IF NOT EXISTS idx_horarios_institucion
    ON horarios_atencion(institucion_id);
    """)

    await client.execute("""
    CREATE INDEX IF NOT EXISTS idx_horarios_profesional
    ON horarios_atencion(profesional_id);
    """)

    await client.execute("""
    CREATE INDEX IF NOT EXISTS idx_especialidades_nombre
    ON especialidades(nombre);
    """)

    print("Indices creados")

    # --------------------------------
    # 2 AGREGAR GEOLOCALIZACION
    # --------------------------------

    print("Agregando columnas lat/lng...")

    try:
        await client.execute("ALTER TABLE instituciones ADD COLUMN lat REAL")
    except:
        pass

    try:
        await client.execute("ALTER TABLE instituciones ADD COLUMN lng REAL")
    except:
        pass

    print("Columnas geográficas listas")

    # --------------------------------
    # 3 TABLA RELACION N:N
    # --------------------------------

    print("Creando tabla institucion_especialidad...")

    await client.execute("""
    CREATE TABLE IF NOT EXISTS institucion_especialidad (
        institucion_id INTEGER NOT NULL,
        especialidad_id INTEGER NOT NULL,
        PRIMARY KEY (institucion_id, especialidad_id)
    );
    """)

    print("Tabla creada")

    # --------------------------------
    # 4 MIGRAR DATOS ACTUALES
    # --------------------------------

    print("Migrando especialidades existentes...")

    rows = await client.execute("""
        SELECT id, especialidad_id
        FROM instituciones
        WHERE especialidad_id IS NOT NULL
    """)

    for row in rows.rows:

        inst_id = row[0]
        spec_id = row[1]

        await client.execute("""
            INSERT OR IGNORE INTO institucion_especialidad
            (institucion_id, especialidad_id)
            VALUES (?, ?)
        """, [inst_id, spec_id])

    print("Migración completada")

    # --------------------------------
    # 5 MEJORAR TABLA PROFESIONALES
    # --------------------------------

    print("Agregando campos profesionales...")

    try:
        await client.execute(
            "ALTER TABLE profesionales ADD COLUMN matricula TEXT"
        )
    except:
        pass

    try:
        await client.execute(
            "ALTER TABLE profesionales ADD COLUMN telefono TEXT"
        )
    except:
        pass

    print("Campos agregados")

    # --------------------------------
    # 6 NORMALIZAR DIA_SEMANA
    # --------------------------------

    print("Creando columna dia_num...")

    try:
        await client.execute(
            "ALTER TABLE horarios_atencion ADD COLUMN dia_num INTEGER"
        )
    except:
        pass

    print("Actualizando valores...")

    await client.execute("""
    UPDATE horarios_atencion SET dia_num =
        CASE LOWER(dia_semana)
            WHEN 'lunes' THEN 1
            WHEN 'martes' THEN 2
            WHEN 'miercoles' THEN 3
            WHEN 'miércoles' THEN 3
            WHEN 'jueves' THEN 4
            WHEN 'viernes' THEN 5
            WHEN 'sabado' THEN 6
            WHEN 'sábado' THEN 6
            WHEN 'domingo' THEN 7
        END
    """)

    print("Normalización de días completada")

    # --------------------------------
    # FINAL
    # --------------------------------

    print("Migración completada con éxito")

    await client.close()


if __name__ == "__main__":
    asyncio.run(migrate_database())