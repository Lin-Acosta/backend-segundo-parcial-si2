from pydantic import BaseModel
from typing import Optional
from datetime import date
from src.modules.actors.schemas import TallerEnIncidente

class CotizacionBase(BaseModel):
    monto: Optional[int] = None
    mensaje: Optional[str] = None
    estado: str = "Solicitada"
    fecha_creacion: Optional[str] = None
    incidente_id: int
    taller_id: int

class CotizacionCreate(BaseModel):
    taller_id: int

class CotizacionOfrecer(BaseModel):
    monto: int
    mensaje: Optional[str] = None

class CotizacionOut(CotizacionBase):
    id: int
    taller: Optional[TallerEnIncidente] = None

    class Config:
        from_attributes = True

class PagoOut(BaseModel):
    id: int
    monto_total: int
    metodo: str
    estado: str
    fecha: Optional[str] = None
    incidente_id: int
    stripe_session_id: Optional[str] = None

    class Config:
        from_attributes = True

class BitacoraBase(BaseModel):
    accion: Optional[str] = None
    descripcion: Optional[str] = None

class BitacoraOut(BitacoraBase):
    id: int
    fecha: Optional[date] = None
    ip: Optional[str] = None
    usuario_id: Optional[int] = None
    usuario_correo: Optional[str] = None
    usuario_rol: Optional[str] = None

    class Config:
        from_attributes = True

class NotificacionBase(BaseModel):
    descripcion: Optional[str] = None
    estado: Optional[str] = "No leída"
    fecha: Optional[str] = None
    titulo: Optional[str] = None

class NotificacionCreate(NotificacionBase):
    pass

class NotificacionOut(NotificacionBase):
    id: int
    usuario_id: int

    class Config:
        from_attributes = True
