from pydantic import BaseModel
from typing import List, Optional
from src.modules.actors.schemas import TallerEnIncidente, MecanicoOut
from src.modules.ai.schemas import AnalisisIAEnIncidente
from src.modules.operations.schemas import CotizacionOut, PagoOut

class EvidenciaBase(BaseModel):
    audio: Optional[str] = None
    descripcion: Optional[str] = None
    fotos: Optional[str] = None

class EvidenciaCreate(EvidenciaBase):
    pass

class Evidencia(EvidenciaBase):
    id: int
    incidente_id: int

    class Config:
        from_attributes = True

class IncidenteBase(BaseModel):
    coordenadagps: Optional[str] = None
    estado: Optional[str] = "Reportado"
    fecha: Optional[str] = None

class IncidenteCreate(IncidenteBase):
    vehiculo_id: int
    evidencia: EvidenciaBase

class Incidente(IncidenteBase):
    id: int
    vehiculoconductor_id: int
    taller_id: Optional[int] = None
    evidencias: List[Evidencia] = []

    class Config:
        from_attributes = True

class IncidenteDetalle(IncidenteBase):
    id: int
    vehiculoconductor_id: int
    taller_id: Optional[int] = None
    evidencias: List[Evidencia] = []
    taller: Optional[TallerEnIncidente] = None
    analisis_ia: Optional[AnalisisIAEnIncidente] = None
    cotizaciones: List[CotizacionOut] = []
    mecanicos: List[MecanicoOut] = []
    pagos: List[PagoOut] = []

    class Config:
        from_attributes = True

class IncidentePendiente(IncidenteDetalle):
    distancia_km: Optional[float] = None

class AsignarTaller(BaseModel):
    taller_id: int

class AsignarMecanicos(BaseModel):
    mecanico_ids: List[int]

class MensajeChatCreate(BaseModel):
    contenido: str

class MensajeChatOut(BaseModel):
    id: int
    contenido: str
    fecha: Optional[str] = None
    incidente_id: int
    usuario_id: int
    nombre_usuario: Optional[str] = None
    rol_usuario: Optional[str] = None

    class Config:
        from_attributes = True

IncidenteDetalle.model_rebuild()
