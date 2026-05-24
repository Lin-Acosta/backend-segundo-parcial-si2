from pydantic import BaseModel
from typing import List, Optional
from datetime import date

class AdministradorBase(BaseModel):
    Usuario: str

class AdministradorCreate(AdministradorBase):
    IdUsuario: int

class Administrador(AdministradorBase):
    IdUsuario: int

    class Config:
        from_attributes = True

class ConductorBase(BaseModel):
    CI: str
    Nombre: str
    Apellidos: str
    Fechanac: date

class ConductorCreate(ConductorBase):
    IdUsuario: int

class ConductorRegistro(BaseModel):
    Correo: str
    Password: str
    CI: str
    Nombre: str
    Apellidos: str
    Fechanac: date

class Conductor(ConductorBase):
    IdUsuario: int

    class Config:
        from_attributes = True

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

class TallerBase(BaseModel):
    Nombre: str
    Direccion: str
    Coordenadas: Optional[str] = None
    Cap: Optional[int] = None
    Capmax: Optional[int] = None

class TallerCreate(TallerBase):
    IdUsuario: int

class Taller(TallerBase):
    Id: int
    IdUsuario: int

    class Config:
        from_attributes = True

class TallerRegistro(TallerBase):
    Correo: str
    Password: str

class MecanicoBase(BaseModel):
    ci: int
    extci: Optional[str] = None
    nombre: str
    apellidos: str
    fechanac: Optional[int] = None

class MecanicoUpdate(BaseModel):
    ci: Optional[int] = None
    extci: Optional[str] = None
    nombre: Optional[str] = None
    apellidos: Optional[str] = None
    fechanac: Optional[int] = None
    estado: Optional[str] = None

class MecanicoRegistro(MecanicoBase):
    correo: str
    password: str

class MecanicoOut(MecanicoBase):
    id: int
    taller_id: Optional[int] = None
    estado: str = "Disponible"

    class Config:
        from_attributes = True

class ServicioTallerOut(BaseModel):
    id: int
    nombre: str

    class Config:
        from_attributes = True

class ServicioTallerCreate(BaseModel):
    nombre: str

class TallerDisponible(BaseModel):
    Id: int
    Nombre: str
    Direccion: str
    Coordenadas: Optional[str] = None
    Cap: Optional[int] = None
    Capmax: Optional[int] = None
    distancia_km: Optional[float] = None
    recomendado_ia: Optional[bool] = False
    servicios: List[ServicioTallerOut] = []

    class Config:
        from_attributes = True

class TallerEnIncidente(BaseModel):
    Id: int
    Nombre: str
    Direccion: str
    Coordenadas: Optional[str] = None
    servicios: List[ServicioTallerOut] = []

    class Config:
        from_attributes = True

class AdminProfileData(BaseModel):
    Usuario: Optional[str] = None

    class Config:
        from_attributes = True

class TallerProfileData(BaseModel):
    Id: Optional[int] = None
    Nombre: Optional[str] = None
    Direccion: Optional[str] = None
    Coordenadas: Optional[str] = None
    Cap: Optional[int] = None
    Capmax: Optional[int] = None
    balance: Optional[int] = None

    class Config:
        from_attributes = True

class ConductorProfileData(BaseModel):
    CI: Optional[str] = None
    Nombre: Optional[str] = None
    Apellidos: Optional[str] = None
    Fechanac: Optional[date] = None

    class Config:
        from_attributes = True

class MecanicoProfileData(BaseModel):
    id: Optional[int] = None
    ci: Optional[int] = None
    nombre: Optional[str] = None
    apellidos: Optional[str] = None
    estado: Optional[str] = None

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
