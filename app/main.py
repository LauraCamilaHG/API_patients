from fastapi import FastAPI
from app.routes import router
from pydantic import BaseModel, Field

app = FastAPI(
    title="API Gestión Hospitalaria",
    description="API para la gestión de pacientes, citas, diagnósticos y medicamentos",
    version="1.0.0"
)

app.include_router(router)


