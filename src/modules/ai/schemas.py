from pydantic import BaseModel
from typing import Optional

class AnalisisIAEnIncidente(BaseModel):
    Clasificacion: Optional[str] = None
    NivelPrioridad: Optional[str] = None
    Resumen: Optional[str] = None
    informacion_valida: Optional[bool] = True

    class Config:
        from_attributes = True

class ReintentarAnalisisPayload(BaseModel):
    nueva_descripcion: str
