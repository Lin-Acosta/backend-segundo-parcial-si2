from pydantic import BaseModel
from typing import List, Optional

class Token(BaseModel):
    access_token: str
    token_type: str
    role: Optional[str] = None
    permisos: Optional[List[str]] = []

class TokenData(BaseModel):
    correo: Optional[str] = None

class PasswordResetRequest(BaseModel):
    correo: str

class PasswordReset(BaseModel):
    token: str
    nueva_password: str

class MensajeResponse(BaseModel):
    message: str

class PermisoBase(BaseModel):
    Nombre: str

class PermisoCreate(PermisoBase):
    pass

class Permiso(PermisoBase):
    Id: int

    class Config:
        from_attributes = True

class RolBase(BaseModel):
    Nombre: str

class RolCreate(RolBase):
    pass

class Rol(RolBase):
    Id: int
    permisos: List[Permiso] = []

    class Config:
        from_attributes = True

class UsuarioBase(BaseModel):
    Correo: str
    IdRol: int

class UsuarioCreate(UsuarioBase):
    Password: str

class UsuarioUpdate(BaseModel):
    Correo: Optional[str] = None
    Password: Optional[str] = None
    IdRol: Optional[int] = None

class Usuario(UsuarioBase):
    Id: int
    rol: Optional[Rol] = None

    class Config:
        from_attributes = True

class FCMTokenUpdate(BaseModel):
    fcm_token: str
