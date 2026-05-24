from sqlalchemy import Column, Integer, String, ForeignKey, Text, Date
from sqlalchemy.orm import relationship
from src.core.database import Base

class Cotizacion(Base):
    __tablename__ = 'Cotizacion'

    id = Column(Integer, primary_key=True, autoincrement=True)
    monto = Column(Integer, nullable=True)
    mensaje = Column(Text, nullable=True)
    estado = Column(String(50), default="Solicitada")
    fecha_creacion = Column(String(50))
    incidente_id = Column(Integer, ForeignKey('Incidente.id', ondelete="CASCADE"), nullable=False)
    taller_id = Column(Integer, ForeignKey('Taller.Id', ondelete="CASCADE"), nullable=False)

    incidente = relationship("Incidente", back_populates="cotizaciones")
    taller = relationship("Taller")

class Pago(Base):
    __tablename__ = 'Pago'

    id = Column(Integer, primary_key=True, autoincrement=True)
    monto_total = Column(Integer, nullable=False)
    metodo = Column(String(50), nullable=False)
    estado = Column(String(50), default="Pendiente")
    stripe_session_id = Column(String(255), nullable=True)
    fecha = Column(String(50))
    incidente_id = Column(Integer, ForeignKey('Incidente.id', ondelete="CASCADE"), nullable=False)

    incidente = relationship("Incidente", back_populates="pagos")

class Bitacora(Base):
    __tablename__ = 'Bitacora'

    id = Column(Integer, primary_key=True, autoincrement=True)
    accion = Column(String(255))
    descripcion = Column(String(255))
    fecha = Column(Date)
    ip = Column(String(255))
    usuario_id = Column(Integer, ForeignKey('Usuario.Id', ondelete="CASCADE"))

    usuario = relationship("Usuario", back_populates="bitacoras")

class Notificacion(Base):
    __tablename__ = 'Notificacion'

    id = Column(Integer, primary_key=True, autoincrement=True)
    descripcion = Column(String(500))
    estado = Column(String(100), default="No leída")
    fecha = Column(String(50))
    titulo = Column(String(255))
    usuario_id = Column(Integer, ForeignKey('Usuario.Id', ondelete="CASCADE"), nullable=False)

    usuario = relationship("Usuario", back_populates="notificaciones")
