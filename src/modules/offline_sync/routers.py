from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel

from src.core.database import get_db
from src.modules.iam.dependencies import get_current_user
from src.modules.iam.models import Usuario
from src.modules.operations.models import Incidente, Evidencia
from src.modules.catalog.models import VehiculoConductor

router = APIRouter(prefix="/offline-sync", tags=["Offline Synchronization"])

# Modelo para recibir datos desde Flutter
class IncidenteOfflineSync(BaseModel):
    local_id: str
    coordenadagps: str
    fecha: str
    descripcion: str

class SyncPayload(BaseModel):
    incidentes: List[IncidenteOfflineSync]

class SyncResponse(BaseModel):
    local_id: str
    server_id: int
    status: str

@router.post("/incidentes", response_model=List[SyncResponse])
def sincronizar_incidentes(
    payload: SyncPayload,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Sincroniza un lote de incidentes creados offline en Flutter."""
    if not current_user.conductor:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Solo conductores pueden sincronizar incidentes."
        )

    # Obtenemos el vehículo activo del conductor (o asumimos el primero para este ejemplo)
    if not current_user.conductor.vehiculo_conductores:
        raise HTTPException(status_code=400, detail="El conductor no tiene vehículos registrados.")
        
    vc_id = current_user.conductor.vehiculo_conductores[0].id
    tenant_id = current_user.tenant_id

    respuestas = []

    for item in payload.incidentes:
        try:
            # 1. Crear el incidente
            nuevo_incidente = Incidente(
                coordenadagps=item.coordenadagps,
                estado="Reportado",
                fecha=item.fecha,
                vehiculoconductor_id=vc_id,
                tenant_id=tenant_id
            )
            db.add(nuevo_incidente)
            db.commit()
            db.refresh(nuevo_incidente)

            # 2. Guardar la descripción en la Evidencia
            nueva_evidencia = Evidencia(
                descripcion=item.descripcion,
                incidente_id=nuevo_incidente.id
            )
            db.add(nueva_evidencia)
            db.commit()

            respuestas.append(SyncResponse(
                local_id=item.local_id,
                server_id=nuevo_incidente.id,
                status="synchronized"
            ))

        except Exception as e:
            db.rollback()
            respuestas.append(SyncResponse(
                local_id=item.local_id,
                server_id=-1,
                status=f"error: {str(e)}"
            ))

    return respuestas
