import os
import libsql_client
from fastapi import FastAPI, HTTPException
from typing import List, Optional
from pydantic import BaseModel
from collections import defaultdict
from contextlib import asynccontextmanager

# --- Configuration ---
TURSO_URL = "https://historiasclinica-smhuglich.aws-us-east-1.turso.io"
TURSO_TOKEN = "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJhIjoicnciLCJleHAiOjE3NzM4NDkwOTYsImlhdCI6MTc3MzI0NDI5NiwiaWQiOiIwMTljZGQ5NC0wODAxLTc4OWQtOWMwNS0xN2MzY2Q1OWZjMDkiLCJyaWQiOiI5ZjAzMDdhYy0wODk3LTQ5YjEtYmQ1OC02MzViMTMxMjQ3MjkifQ.lXR31lF8cKw6imVLcFGbKGAMPcdZSDS0vQwjvXXGQMAvPzAUGHXDVhfTj3qHuPO73z3gaCYdQPMv5SZlUbz8Aw"

# Use a global client variable
db_client = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global db_client
    # Initialize Turso Client inside the event loop
    db_client = libsql_client.create_client(TURSO_URL, auth_token=TURSO_TOKEN)
    yield
    # Close client on shutdown
    await db_client.close()

app = FastAPI(title="Medical App API", lifespan=lifespan)

# --- Models ---
class Specialty(BaseModel):
    id: int
    nombre: str

class Schedule(BaseModel):
    prof: str
    dia_num: int
    inicio: str
    fin: str

class InstitutionInfo(BaseModel):
    id: int
    nombre: str
    direccion: str
    telefono: Optional[str]
    lat: Optional[float]
    lng: Optional[float]

class InstitutionData(BaseModel):
    info: InstitutionInfo
    scheds: List[Schedule]

# --- Endpoints ---

@app.get("/specialties", response_model=List[Specialty])
async def get_specialties():
    try:
        rs = await db_client.execute("SELECT id, nombre FROM especialidades ORDER BY nombre")
        return [{"id": r[0], "nombre": r[1]} for r in rs.rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/institutions/{specialty_id}", response_model=List[InstitutionData])
async def get_institutions(specialty_id: int):
    try:
        query = """
        SELECT
            i.id, i.nombre, i.direccion, i.telefono, i.lat, i.lng,
            p.nombre, p.apellido, h.dia_num, h.hora_inicio, h.hora_fin
        FROM instituciones i
        JOIN institucion_especialidad ie ON ie.institucion_id = i.id
        LEFT JOIN horarios_atencion h ON h.institucion_id = i.id
        LEFT JOIN profesionales p ON p.id = h.profesional_id
        WHERE ie.especialidad_id = ?
        ORDER BY i.nombre, h.dia_num, h.hora_inicio
        """
        rs = await db_client.execute(query, [specialty_id])
        
        data = defaultdict(lambda: {"info": {}, "scheds": []})
        
        for row in rs.rows:
            inst_id = row[0]
            data[inst_id]["info"] = {
                "id": inst_id,
                "nombre": row[1],
                "direccion": row[2],
                "telefono": row[3],
                "lat": row[4],
                "lng": row[5],
            }
            if row[6] is not None:
                data[inst_id]["scheds"].append({
                    "prof": f"{row[6]} {row[7]}",
                    "dia_num": row[8],
                    "inicio": row[9],
                    "fin": row[10]
                })
        
        return list(data.values())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
