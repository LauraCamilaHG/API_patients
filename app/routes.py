from fastapi import APIRouter, HTTPException, Depends
from typing import List
from .models import Paciente, Especialista, Cita, CitaCreate
from .database import get_db_connection
from datetime import date, datetime
import mysql.connector
from datetime import timezone

router = APIRouter()

@router.post("/pacientes/bulk", response_model=List[Paciente], tags=["Pacientes"])
async def crear_pacientes_bulk(pacientes: List[Paciente]):
    """
    Crea múltiples pacientes en la base de datos
    """
    db = get_db_connection()
    cursor = db.cursor()
    try:
        query = """
        INSERT INTO pacientes (documento, nombre, fecha_nacimiento, telefono)
        VALUES (%s, %s, %s, %s)
        """
        
        # Preparar los valores para la inserción
        values = [
            (
                paciente.documento,
                paciente.nombre,
                paciente.fecha_nacimiento,
                paciente.telefono
            ) 
            for paciente in pacientes
        ]
        
        # Ejecutar la inserción múltiple
        cursor.executemany(query, values)
        db.commit()
        
        # Obtener el ID del primer paciente insertado
        first_id = cursor.lastrowid
        
        # Crear lista de pacientes creados con sus IDs
        pacientes_creados = []
        for idx, paciente in enumerate(pacientes):
            paciente_dict = paciente.model_dump()
            paciente_dict['id_paciente'] = first_id + idx
            pacientes_creados.append(Paciente(**paciente_dict))
        
        return pacientes_creados

    except Exception as e:
        db.rollback()
        print(f"Error al crear pacientes: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al crear los pacientes: {str(e)}"
        )
    finally:
        cursor.close()
        db.close()


@router.get("/pacientes/", response_model=List[Paciente], tags=["Pacientes"])
async def listar_pacientes():
    """
    Obtiene la lista de todos los pacientes registrados en la base de datos
    """
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    
    try:
        # Consulta SQL para obtener todos los pacientes
        query = """
        SELECT 
            id_paciente,
            documento,
            nombre,
            fecha_nacimiento,
            telefono
        FROM pacientes
        ORDER BY nombre ASC
        """
        
        cursor.execute(query)
        pacientes = cursor.fetchall()
        
        # Convertir los resultados a objetos Paciente
        return [Paciente(**paciente) for paciente in pacientes]
        
    except Exception as e:
        print(f"Error al consultar pacientes: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al consultar los pacientes: {str(e)}"
        )
    finally:
        cursor.close()
        db.close()

# POST Especialistas
@router.post("/especialistas/bulk", response_model=List[Especialista], tags=["Especialistas"])
async def crear_especialistas_bulk(especialistas: List[Especialista]):
    db = get_db_connection()
    cursor = db.cursor()
    try:
        query = """
        INSERT INTO especialistas (documento, nombre, especialidad)
        VALUES (%s, %s, %s)
        """
        values = [
            (
                especialista.documento,
                especialista.nombre,
                especialista.especialidad
            ) 
            for especialista in especialistas
        ]
        cursor.executemany(query, values)
        db.commit()
        
        first_id = cursor.lastrowid
        especialistas_creados = []
        for idx, especialista in enumerate(especialistas):
            especialista_dict = especialista.model_dump()
            especialista_dict['id_especialista'] = first_id + idx
            especialistas_creados.append(Especialista(**especialista_dict))
        
        return especialistas_creados
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        db.close()

# GET Especialistas
@router.get("/especialistas/", response_model=List[Especialista], tags=["Especialistas"])
async def listar_especialistas():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM especialistas ORDER BY nombre")
        return [Especialista(**esp) for esp in cursor.fetchall()]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        db.close()

# POST Citas
@router.post("/citas/{id_paciente}/{id_especialista}/", response_model=List[Cita], tags=["Citas"])
async def crear_citas_bulk(id_paciente: int, id_especialista: int, citas: List[CitaCreate]):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Verificar si existe el paciente y especialista
        cursor.execute("SELECT * FROM pacientes WHERE id_paciente = %s", (id_paciente,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail=f"Paciente {id_paciente} no encontrado")
        
        cursor.execute("SELECT * FROM especialistas WHERE id_especialista = %s", (id_especialista,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail=f"Especialista {id_especialista} no encontrado")
        
        citas_creadas = []
        for cita in citas:
            try:
                fecha_hora_utc = cita.fecha_hora.astimezone(timezone.utc).replace(tzinfo=None)
                
                query = """
                INSERT INTO citas (id_paciente, id_especialista, fecha_hora, estado)
                VALUES (%s, %s, %s, %s)
                """
                values = (id_paciente, id_especialista, fecha_hora_utc, cita.estado)
                
                cursor.execute(query, values)
                id_cita = cursor.lastrowid
                citas_creadas.append(Cita(
                    id_cita=id_cita,
                    id_paciente=id_paciente,
                    id_especialista=id_especialista,
                    fecha_hora=cita.fecha_hora,
                    estado=cita.estado
                ))
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error al crear cita: {str(e)}")
        
        conn.commit()
        return citas_creadas
    
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error en la operación: {str(e)}")
    finally:
        cursor.close()
        conn.close()

# GET Citas
@router.get("/citas/", response_model=List[Cita], tags=["Citas"])
async def listar_citas():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        query = """
        SELECT 
            c.*,
            p.nombre as nombre_paciente,
            e.nombre as nombre_especialista
        FROM citas c
        JOIN pacientes p ON c.id_paciente = p.id_paciente
        JOIN especialistas e ON c.id_especialista = e.id_especialista
        ORDER BY c.fecha_hora
        """
        cursor.execute(query)
        citas = cursor.fetchall()
        return [Cita(**cita) for cita in citas]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()
