from datetime import date, datetime
from pydantic import BaseModel

class Paciente(BaseModel):
    id_paciente: int | None = None
    documento: str      
    nombre: str        
    fecha_nacimiento: date
    telefono: str      

class MedicamentoCreate(BaseModel):
    nombre: str
    descripcion: str
    stock: int

class Medicamento(MedicamentoCreate):
    id_medicamento: int | None = None

class DiagnosticoCreate(BaseModel):
    descripcion: str
    fecha_diagnostico: date

class Diagnostico(BaseModel):
    id_diagnostico: int | None = None
    id_cita: int
    id_paciente: int
    descripcion: str
    fecha_diagnostico: date
    nombre_paciente: str | None = None
    nombre_especialista: str | None = None

class FormulaCreate(BaseModel):
    id_diagnostico: int
    id_medicamento: int
    dosis: str
    duracion: int

class Formula(FormulaCreate):
    id_formula: int | None = None
    nombre_medicamento: str | None = None
    descripcion_diagnostico: str | None = None

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