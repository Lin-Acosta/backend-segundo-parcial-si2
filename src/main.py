from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from src.core.database import engine, Base, get_db

from src.modules.security.models import Usuario, Rol, Permiso
from src.modules.actors.models import Administrador, Conductor, Vehiculo, VehiculoConductor, Taller, Mecanico, ServicioTaller
from src.modules.emergencies.models import Incidente, Evidencia, IncidenteMecanico, MensajeChat
from src.modules.ai.models import AnalisisIA
from src.modules.operations.models import Cotizacion, Pago, Bitacora, Notificacion

import os

# Crear todas las tablas en la base de datos
Base.metadata.create_all(bind=engine)

from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

app = FastAPI(
    title="Backend API - Plataforma Inteligente de Atención de Emergencias Vehiculares",
    description="API con arquitectura modular para el backend de emergencias",
    version="1.0.0"
)

# Habilitar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from src.modules.security.routers import auth, users, roles
from src.modules.actors.routers import mecanicos, vehiculos, profile
from src.modules.emergencies.routers import incidentes
from src.modules.ai.routers import ia
from src.modules.operations.routers import bitacora, notificaciones, pagos, reportes

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(roles.router)
app.include_router(mecanicos.router)
app.include_router(vehiculos.router)
app.include_router(incidentes.router)
app.include_router(bitacora.router)
app.include_router(notificaciones.router)
app.include_router(profile.router)
app.include_router(ia.router)
app.include_router(pagos.router)
app.include_router(reportes.router)

# Servir archivos estáticos (fotos de incidentes)
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

@app.get("/")
def read_root():
    return {"message": "Bienvenido a la API del proyecto de Backend Modular"}

@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    try:
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        return {"status": "error", "database": "disconnected", "details": str(e)}
