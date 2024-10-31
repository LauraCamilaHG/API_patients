from fastapi import APIRouter, HTTPException, Depends
from typing import List
from .models import Paciente, Especialista, Cita, CitaCreate, Medicamento, Formula, Diagnostico, DiagnosticoCreate
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

@router.post("/medicamentos/bulk", response_model=List[Medicamento], tags=["Medicamentos"])
async def crear_medicamentos_bulk(medicamentos: List[Medicamento]):
    """
    Crea múltiples medicamentos en la base de datos
    """
    db = get_db_connection()
    cursor = db.cursor()
    try:
        query = """
        INSERT INTO medicamentos (nombre, descripcion, stock)
        VALUES (%s, %s, %s)
        """
        
        medicamentos_creados = []
        for medicamento in medicamentos:
            values = (
                medicamento.nombre,
                medicamento.descripcion,
                medicamento.stock
            )
            
            cursor.execute(query, values)
            id_medicamento = cursor.lastrowid
            
            medicamentos_creados.append(Medicamento(
                id_medicamento=id_medicamento,
                nombre=medicamento.nombre,
                descripcion=medicamento.descripcion,
                stock=medicamento.stock
            ))
        
        db.commit()
        
        return medicamentos_creados

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error al crear los medicamentos: {str(e)}"
        )
    finally:
        cursor.close()
        db.close()

@router.get("/medicamentos/", response_model=List[Medicamento], tags=["Medicamentos"])
async def listar_medicamentos():
    """
    Obtiene la lista de todos los medicamentos registrados
    """
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    
    try:
        query = """
        SELECT 
            id_medicamento,
            nombre,
            descripcion,
            stock
        FROM medicamentos
        ORDER BY nombre ASC
        """
        
        cursor.execute(query)
        medicamentos = cursor.fetchall()
        return [Medicamento(**medicamento) for medicamento in medicamentos]
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al consultar los medicamentos: {str(e)}"
        )
    finally:
        cursor.close()
        db.close()

@router.post("/formulas/bulk", response_model=List[Formula], tags=["Fórmulas"])
async def crear_formulas_bulk(formulas: List[Formula]):
    """
    Crea múltiples fórmulas médicas en la base de datos
    """
    db = get_db_connection()
    cursor = db.cursor()
    
    try:
        # Primero verificamos que existan los diagnósticos y medicamentos
        for formula in formulas:
            cursor.execute("SELECT * FROM diagnosticos WHERE id_diagnostico = %s", 
                         (formula.id_diagnostico,))
            if not cursor.fetchone():
                raise HTTPException(
                    status_code=404,
                    detail=f"Diagnóstico {formula.id_diagnostico} no encontrado"
                )
            
            cursor.execute("SELECT * FROM medicamentos WHERE id_medicamento = %s", 
                         (formula.id_medicamento,))
            if not cursor.fetchone():
                raise HTTPException(
                    status_code=404,
                    detail=f"Medicamento {formula.id_medicamento} no encontrado"
                )
        
        query = """
        INSERT INTO formulas (id_diagnostico, id_medicamento, dosis, duracion)
        VALUES (%s, %s, %s, %s)
        """
        
        formulas_creadas = []
        for formula in formulas:
            values = (
                formula.id_diagnostico,
                formula.id_medicamento,
                formula.dosis,
                formula.duracion
            )
            
            cursor.execute(query, values)
            id_formula = cursor.lastrowid
            
            formulas_creadas.append(Formula(
                id_formula=id_formula,
                id_diagnostico=formula.id_diagnostico,
                id_medicamento=formula.id_medicamento,
                dosis=formula.dosis,
                duracion=formula.duracion
            ))
        
        db.commit()
        return formulas_creadas

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error al crear las fórmulas: {str(e)}"
        )
    finally:
        cursor.close()
        db.close()

@router.get("/formulas/", response_model=List[Formula], tags=["Fórmulas"])
async def listar_formulas():
    """
    Obtiene la lista de todas las fórmulas médicas con información detallada
    """
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    
    try:
        query = """
        SELECT 
            f.*,
            m.nombre as nombre_medicamento,
            d.descripcion as descripcion_diagnostico
        FROM formulas f
        JOIN medicamentos m ON f.id_medicamento = m.id_medicamento
        JOIN diagnosticos d ON f.id_diagnostico = d.id_diagnostico
        ORDER BY f.id_formula DESC
        """
        
        cursor.execute(query)
        formulas = cursor.fetchall()
        return [Formula(**formula) for formula in formulas]
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al consultar las fórmulas: {str(e)}"
        )
    finally:
        cursor.close()
        db.close()

# Endpoint adicional para obtener fórmulas por diagnóstico
@router.get("/formulas/diagnostico/{id_diagnostico}", response_model=List[Formula], tags=["Fórmulas"])
async def obtener_formulas_por_diagnostico(id_diagnostico: int):
    """
    Obtiene todas las fórmulas asociadas a un diagnóstico específico
    """
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    
    try:
        query = """
        SELECT 
            f.*,
            m.nombre as nombre_medicamento
        FROM formulas f
        JOIN medicamentos m ON f.id_medicamento = m.id_medicamento
        WHERE f.id_diagnostico = %s
        """
        
        cursor.execute(query, (id_diagnostico,))
        formulas = cursor.fetchall()
        
        if not formulas:
            raise HTTPException(
                status_code=404,
                detail=f"No se encontraron fórmulas para el diagnóstico {id_diagnostico}"
            )
            
        return [Formula(**formula) for formula in formulas]
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al consultar las fórmulas: {str(e)}"
        )
    finally:
        cursor.close()
        db.close()

# Mantener solo un endpoint POST para crear diagnósticos
@router.post("/diagnosticos/{id_cita}/{id_paciente}/", response_model=Diagnostico, tags=["Diagnósticos"])
async def crear_diagnostico(
    id_cita: int,
    id_paciente: int,
    diagnostico: DiagnosticoCreate
):
    """
    Crea un diagnóstico en la base de datos.
    El id_cita y id_paciente se proporcionan como parámetros en la URL.
    """
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    
    try:
        # Verificar que exista la cita
        cursor.execute("""
            SELECT c.*, p.nombre as nombre_paciente, e.nombre as nombre_especialista 
            FROM citas c
            JOIN pacientes p ON c.id_paciente = p.id_paciente
            JOIN especialistas e ON c.id_especialista = e.id_especialista
            WHERE c.id_cita = %s AND c.id_paciente = %s
        """, (id_cita, id_paciente))
        
        cita = cursor.fetchone()
        if not cita:
            raise HTTPException(
                status_code=404,
                detail=f"No se encontró una cita con ID {id_cita} para el paciente {id_paciente}"
            )
        
        # Insertar el diagnóstico
        query = """
        INSERT INTO diagnosticos (id_cita, id_paciente, descripcion, fecha_diagnostico)
        VALUES (%s, %s, %s, %s)
        """
        
        values = (
            id_cita,
            id_paciente,
            diagnostico.descripcion,
            diagnostico.fecha_diagnostico
        )
        
        cursor.execute(query, values)
        id_diagnostico = cursor.lastrowid
        
        # Crear el objeto de respuesta
        diagnostico_creado = {
            "id_diagnostico": id_diagnostico,
            "id_cita": id_cita,
            "id_paciente": id_paciente,
            "descripcion": diagnostico.descripcion,
            "fecha_diagnostico": diagnostico.fecha_diagnostico,
            "nombre_paciente": cita["nombre_paciente"],
            "nombre_especialista": cita["nombre_especialista"]
        }
        
        db.commit()
        return Diagnostico(**diagnostico_creado)

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error al crear el diagnóstico: {str(e)}"
        )
    finally:
        cursor.close()
        db.close()

@router.get("/diagnosticos/", response_model=List[Diagnostico], tags=["Diagnósticos"])
async def listar_diagnosticos():
    """
    Obtiene la lista de todos los diagnósticos con información detallada
    """
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    
    try:
        query = """
        SELECT 
            d.*,
            p.nombre as nombre_paciente,
            e.nombre as nombre_especialista
        FROM diagnosticos d
        JOIN citas c ON d.id_cita = c.id_cita
        JOIN pacientes p ON c.id_paciente = p.id_paciente
        JOIN especialistas e ON c.id_especialista = e.id_especialista
        ORDER BY d.fecha_diagnostico DESC
        """
        
        cursor.execute(query)
        diagnosticos = cursor.fetchall()
        return [Diagnostico(**diagnostico) for diagnostico in diagnosticos]
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al consultar los diagnósticos: {str(e)}"
        )
    finally:
        cursor.close()
        db.close()

# Endpoint adicional para obtener diagnósticos por paciente
@router.get("/diagnosticos/paciente/{id_paciente}", response_model=List[Diagnostico], tags=["Diagnósticos"])
async def obtener_diagnosticos_por_paciente(id_paciente: int):
    """
    Obtiene todos los diagnósticos de un paciente específico
    """
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    
    try:
        query = """
        SELECT 
            d.*,
            p.nombre as nombre_paciente,
            e.nombre as nombre_especialista
        FROM diagnosticos d
        JOIN citas c ON d.id_cita = c.id_cita
        JOIN pacientes p ON c.id_paciente = p.id_paciente
        JOIN especialistas e ON c.id_especialista = e.id_especialista
        WHERE p.id_paciente = %s
        ORDER BY d.fecha_diagnostico DESC
        """
        
        cursor.execute(query, (id_paciente,))
        diagnosticos = cursor.fetchall()
        
        if not diagnosticos:
            raise HTTPException(
                status_code=404,
                detail=f"No se encontraron diagnósticos para el paciente {id_paciente}"
            )
            
        return [Diagnostico(**diagnostico) for diagnostico in diagnosticos]
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al consultar los diagnósticos: {str(e)}"
        )
    finally:
        cursor.close()
        db.close()
