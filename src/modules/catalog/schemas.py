from pydantic import BaseModel
from datetime import date
from typing import Optional, List

# ── Conductor ─────────────────────────────────────────────────────────────────

class ConductorBase(BaseModel):
    CI: str
    Nombre: str
    Apellidos: str
    Fechanac: date

class ConductorRegistro(ConductorBase):
    Correo: str
    Password: str

class ConductorOut(ConductorBase):
    IdUsuario: int
    class Config:
        from_attributes = True

# ── Taller ────────────────────────────────────────────────────────────────────

class TallerBase(BaseModel):
    Nombre: str
    Direccion: str
    Coordenadas: Optional[str] = None
    Cap: Optional[int] = 0
    Capmax: Optional[int] = 10

class TallerRegistro(TallerBase):
    Correo: str
    Password: str

class TallerOut(TallerBase):
    Id: int
    balance: int
    IdUsuario: int
    class Config:
        from_attributes = True

class TallerDisponible(TallerOut):
    distancia_km: float

class ServicioTallerBase(BaseModel):
    nombre: str

class ServicioTallerCreate(ServicioTallerBase):
    pass

class ServicioTallerOut(ServicioTallerBase):
    id: int
    taller_id: int
    class Config:
        from_attributes = True

# ── Vehiculo ──────────────────────────────────────────────────────────────────

class VehiculoBase(BaseModel):
    Marca: Optional[str] = None
    Modelo: Optional[str] = None
    Placa: Optional[str] = None
    Poliza: Optional[str] = None
    Categoria: Optional[str] = None
    Año: Optional[int] = None

class VehiculoCreate(VehiculoBase):
    pass

class Vehiculo(VehiculoBase):
    Id: int
    class Config:
        from_attributes = True

# ── Mecanico ──────────────────────────────────────────────────────────────────

class MecanicoBase(BaseModel):
    ci: int
    extci: Optional[str] = None
    nombre: str
    apellidos: str
    fechanac: Optional[int] = None
    estado: Optional[str] = "Disponible"

class MecanicoRegistro(MecanicoBase):
    correo: str
    password: str

class MecanicoUpdate(BaseModel):
    ci: Optional[int] = None
    extci: Optional[str] = None
    nombre: Optional[str] = None
    apellidos: Optional[str] = None
    fechanac: Optional[int] = None
    estado: Optional[str] = None

class MecanicoOut(MecanicoBase):
    id: int
    taller_id: Optional[int] = None
    class Config:
        from_attributes = True

# ── Perfil (Combinado) ────────────────────────────────────────────────────────

class AdminProfileData(BaseModel):
    Usuario: str
    class Config:
        from_attributes = True

class TallerProfileData(BaseModel):
    Id: int
    Nombre: str
    Direccion: str
    Coordenadas: Optional[str] = None
    Cap: int
    Capmax: int
    balance: int
    class Config:
        from_attributes = True

class ConductorProfileData(BaseModel):
    CI: str
    Nombre: str
    Apellidos: str
    Fechanac: date
    class Config:
        from_attributes = True

class MecanicoProfileData(BaseModel):
    id: int
    ci: int
    nombre: str
    apellidos: str
    estado: str
    class Config:
        from_attributes = True

class ProfileOut(BaseModel):
    Id: int
    Correo: str
    rol_nombre: Optional[str] = None
    administrador: Optional[AdminProfileData] = None
    taller: Optional[TallerProfileData] = None
    conductor: Optional[ConductorProfileData] = None
    mecanico: Optional[MecanicoProfileData] = None
    class Config:
        from_attributes = True

class ProfileUpdate(BaseModel):
    Correo: Optional[str] = None
    Password: Optional[str] = None
    admin_usuario: Optional[str] = None
    taller_nombre: Optional[str] = None
    taller_direccion: Optional[str] = None
    taller_coordenadas: Optional[str] = None
    taller_cap: Optional[int] = None
    taller_capmax: Optional[int] = None
    conductor_ci: Optional[str] = None
    conductor_nombre: Optional[str] = None
    conductor_apellidos: Optional[str] = None
    conductor_fechanac: Optional[date] = None
    mecanico_estado: Optional[str] = None

class UbicacionUpdate(BaseModel):
    Coordenadas: str
    Direccion: Optional[str] = None
