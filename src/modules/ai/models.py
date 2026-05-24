from sqlalchemy import Column, Integer, String, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from src.core.database import Base

class AnalisisIA(Base):
    __tablename__ = 'AnalisisIA'

    id = Column(Integer, primary_key=True, autoincrement=True)
    Clasificacion = Column(String(100), nullable=True)
    NivelPrioridad = Column(String(50), nullable=True)
    Resumen = Column(Text, nullable=True)
    TranscripcionAudio = Column(Text, nullable=True)
    informacion_valida = Column(Boolean, nullable=True, default=True)
    incidente_id = Column(Integer, ForeignKey('Incidente.id', ondelete="CASCADE"), unique=True)

    incidente = relationship("Incidente", back_populates="analisis_ia")
