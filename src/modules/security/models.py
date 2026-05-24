from sqlalchemy import Column, Integer, String, ForeignKey, Table
from sqlalchemy.orm import relationship
from src.core.database import Base

rol_permiso_table = Table(
    'Rol_Permiso',
    Base.metadata,
    Column('IdRol', Integer, ForeignKey('Rol.Id'), primary_key=True),
    Column('IdPermiso', Integer, ForeignKey('Permiso.Id'), primary_key=True)
)

class Permiso(Base):
    __tablename__ = 'Permiso'

    Id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    Nombre = Column(String(255), nullable=False)

    roles = relationship("Rol", secondary=rol_permiso_table, back_populates="permisos")


class Rol(Base):
    __tablename__ = 'Rol'

    Id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    Nombre = Column(String(255), nullable=False)

    permisos = relationship("Permiso", secondary=rol_permiso_table, back_populates="roles")
    usuarios = relationship("Usuario", back_populates="rol")


class Usuario(Base):
    __tablename__ = 'Usuario'

    Id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    Correo = Column(String(255), nullable=False, unique=True, index=True)
    Password = Column(String(255), nullable=False)
    IdRol = Column(Integer, ForeignKey('Rol.Id'), nullable=False)
    fcm_token = Column(String(255), nullable=True)

    rol = relationship("Rol", back_populates="usuarios")
    talleres = relationship("Taller", back_populates="usuario")
    administrador = relationship("Administrador", uselist=False, back_populates="usuario")
    conductor = relationship("Conductor", uselist=False, back_populates="usuario")
    mecanico = relationship("Mecanico", uselist=False, back_populates="usuario")
    bitacoras = relationship("Bitacora", back_populates="usuario")
    notificaciones = relationship("Notificacion", back_populates="usuario", cascade="all, delete-orphan")
