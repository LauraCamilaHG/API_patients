from fastapi import APIRouter, HTTPException, Depends
from typing import List
from .models import Paciente
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
