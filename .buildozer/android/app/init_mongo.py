import certifi
from pymongo import MongoClient
from pymongo.server_api import ServerApi

def init_mongodb():
    uri = "mongodb+srv://sergiohuglich77_db_user:yFja0pPRBJsE5idl@historiasclinica.a9e1jdt.mongodb.net/"
    print("Conectando a MongoDB para inicializar la base de datos...")
    
    client = MongoClient(uri, server_api=ServerApi('1'), tlsCAFile=certifi.where())
    jls_extract_var = 'historiasclinica'
    db = client[jls_extract_var]
    
    try:
        # 1. Limpiar colecciones existentes (opcional, para empezar de cero)
        cols_to_drop = ['especialidades', 'instituciones', 'profesionales', 'horarios_atencion']
        for col in cols_to_drop:
            db[col].drop()
            print(f"Colección '{col}' preparada.")

        # 2. Insertar Especialidades
        print("Insertando especialidades...")
        especialidades_data = [
            {'nombre': 'Cardiología'}, {'nombre': 'Pediatría'}, {'nombre': 'Dermatología'},
            {'nombre': 'Ginecología'}, {'nombre': 'Neurología'}, {'nombre': 'Traumatología'},
            {'nombre': 'Oftalmología'}, {'nombre': 'Psiquiatría'}, {'nombre': 'Odontología'},
            {'nombre': 'Nutrición'}
        ]
        db.especialidades.insert_many(especialidades_data)
        
        # Mapear nombres a IDs de MongoDB para las relaciones
        spec_map = {doc['nombre']: doc['_id'] for doc in db.especialidades.find()}

        # 3. Insertar Profesionales
        print("Insertando profesionales...")
        profesionales_data = [
            {'nombre': 'Juan', 'apellido': 'Pérez'},
            {'nombre': 'María', 'apellido': 'García'},
            {'nombre': 'Luis', 'apellido': 'Rodríguez'},
            {'nombre': 'Ana', 'apellido': 'Sánchez'},
            {'nombre': 'Carlos', 'apellido': 'López'}
        ]
        db.profesionales.insert_many(profesionales_data)
        prof_map = {f"{doc['nombre']} {doc['apellido']}": doc['_id'] for doc in db.profesionales.find()}

        # 4. Insertar Instituciones
        print("Insertando instituciones...")
        instituciones_data = [
            {'nombre': 'Hospital Central', 'direccion': 'Av. San Martín 123', 'telefono': '2604449876', 'especialidad_id': spec_map['Cardiología']},
            {'nombre': 'Clínica del Sol', 'direccion': 'Calle Belgrano 456', 'telefono': '2604555876', 'especialidad_id': spec_map['Cardiología']},
            {'nombre': 'Centro Médico Norte', 'direccion': 'Ruta 40 Km 10', 'telefono': '83747384949', 'especialidad_id': spec_map['Pediatría']},
            {'nombre': 'Instituto Pediátrico', 'direccion': 'Paso de los Andes 789', 'telefono': '83736729', 'especialidad_id': spec_map['Pediatría']},
            {'nombre': 'Sanatorio Anchorena', 'direccion': 'Urquiza 321', 'telefono': '393993993', 'especialidad_id': spec_map['Dermatología']}
        ]
        db.instituciones.insert_many(instituciones_data)
        inst_map = {doc['nombre']: doc['_id'] for doc in db.instituciones.find()}

        # 5. Insertar Horarios de Atención
        print("Insertando horarios...")
        horarios_data = [
            {'profesional_id': prof_map['Juan Pérez'], 'institucion_id': inst_map['Hospital Central'], 'dia_semana': 'Lunes', 'hora_inicio': '08:00', 'hora_fin': '12:00'},
            {'profesional_id': prof_map['María García'], 'institucion_id': inst_map['Hospital Central'], 'dia_semana': 'Martes', 'hora_inicio': '14:00', 'hora_fin': '18:00'},
            {'profesional_id': prof_map['Luis Rodríguez'], 'institucion_id': inst_map['Clínica del Sol'], 'dia_semana': 'Miércoles', 'hora_inicio': '09:00', 'hora_fin': '13:00'},
            {'profesional_id': prof_map['Ana Sánchez'], 'institucion_id': inst_map['Centro Médico Norte'], 'dia_semana': 'Jueves', 'hora_inicio': '10:00', 'hora_fin': '16:00'},
            {'profesional_id': prof_map['Carlos López'], 'institucion_id': inst_map['Instituto Pediátrico'], 'dia_semana': 'Viernes', 'hora_inicio': '08:00', 'hora_fin': '14:00'}
        ]
        db.horarios_atencion.insert_many(horarios_data)

        print("\n✅ ¡Base de datos 'historiasclinica' inicializada con éxito en MongoDB Atlas!")
        
    except Exception as e:
        print(f"\n❌ Falló la inicialización: {e}")

if __name__ == "__main__":
    init_mongodb()
