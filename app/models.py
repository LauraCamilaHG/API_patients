from datetime import date, datetime
from pydantic import BaseModel

class Paciente(BaseModel):
    id_paciente: int | None = None
    documento: str      
    nombre: str        
    fecha_nacimiento: date
    telefono: str      

class Medicamento(BaseModel):
    id_medicamento: int | None = None
    nombre: str        
    descripcion: str   
    stock: int        

class Diagnostico(BaseModel):
    id_diagnostico: int | None = None
    id_cita: int
    descripcion: str   
    fecha_diagnostico: date

class Formula(BaseModel):
    id_formula: int | None = None
    id_diagnostico: int
    id_medicamento: int
    dosis: str        
    duracion: int     

class Especialista(BaseModel):
    id_especialista: int | None = None
    documento: str     
    nombre: str       
    especialidad: str  

class CitaCreate(BaseModel):
    fecha_hora: datetime
    estado: str

class Cita(BaseModel):
    id_cita: int | None = None
    id_paciente: int
    id_especialista: int
    fecha_hora: datetime
    estado: str
    nombre_paciente: str | None = None
    nombre_especialista: str | None = None