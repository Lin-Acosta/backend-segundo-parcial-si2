from sqlalchemy import Column, Integer, String, ForeignKey, Text
from sqlalchemy.orm import relationship
from src.core.database import Base

class IncidenteMecanico(Base):
    __tablename__ = 'IncidenteMecanico'
    incidente_id = Column(Integer, ForeignKey('Incidente.id', ondelete="CASCADE"), primary_key=True)
    mecanico_id = Column(Integer, ForeignKey('Mecanico.id', ondelete="CASCADE"), primary_key=True)

class Incidente(Base):
    __tablename__ = 'Incidente'

    id = Column(Integer, primary_key=True, autoincrement=True)
    coordenadagps = Column(String(255))
    estado = Column(String(50), default="Reportado")
    fecha = Column(String(50))
    vehiculoconductor_id = Column(Integer, ForeignKey('VehiculoConductor.id', ondelete="CASCADE"), nullable=False)
    taller_id = Column(Integer, ForeignKey('Taller.Id', ondelete="SET NULL"), nullable=True)

    vehiculoconductor = relationship("VehiculoConductor", back_populates="incidentes")
    evidencias = relationship("Evidencia", back_populates="incidente", cascade="all, delete-orphan")
    taller = relationship("Taller", foreign_keys=[taller_id])
    analisis_ia = relationship("AnalisisIA", uselist=False, back_populates="incidente", cascade="all, delete-orphan")
    cotizaciones = relationship("Cotizacion", back_populates="incidente", cascade="all, delete-orphan")
    mecanicos = relationship("Mecanico", secondary="IncidenteMecanico", back_populates="incidentes_asignados")
    pagos = relationship("Pago", back_populates="incidente", cascade="all, delete-orphan")
    mensajes = relationship("MensajeChat", back_populates="incidente", cascade="all, delete-orphan")

class Evidencia(Base):
    __tablename__ = 'Evidencia'

    id = Column(Integer, primary_key=True, autoincrement=True)
    audio = Column(String(2000), nullable=True) 
    descripcion = Column(String(5000), nullable=True)
    fotos = Column(Text, nullable=True)
    incidente_id = Column(Integer, ForeignKey('Incidente.id', ondelete="CASCADE"), nullable=False)

    incidente = relationship("Incidente", back_populates="evidencias")

class MensajeChat(Base):
    __tablename__ = 'MensajeChat'

    id = Column(Integer, primary_key=True, autoincrement=True)
    contenido = Column(Text, nullable=False)
    fecha = Column(String(50))
    incidente_id = Column(Integer, ForeignKey('Incidente.id', ondelete="CASCADE"), nullable=False)
    usuario_id = Column(Integer, ForeignKey('Usuario.Id', ondelete="CASCADE"), nullable=False)

    incidente = relationship("Incidente", back_populates="mensajes")
    usuario = relationship("Usuario")
