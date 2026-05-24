from src.core.database import get_db
from src.shared.dependencies import get_current_user
from src.modules.actors.models import Vehiculo, VehiculoConductor
from src.modules.security.models import Usuario
from src.modules.actors.schemas import Vehiculo as VehiculoSchema, VehiculoCreate

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List


router = APIRouter(
    prefix="/vehiculos",
    tags=["Vehículos"]
)

@router.post("/", response_model=VehiculoSchema)
def registrar_vehiculo(
    vehiculo: VehiculoCreate, 
    db: Session = Depends(get_db), 
    current_user: Usuario = Depends(get_current_user)
):
    # Validar que el usuario que intenta registrar sea un conductor
    if not current_user.conductor:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Debe tener un perfil de conductor para registrar vehículos"
        )
    
    # Comprobar si el vehículo ya existe en la base de datos por placa
    db_vehiculo = None
    if vehiculo.Placa:
        db_vehiculo = db.query(Vehiculo).filter(Vehiculo.Placa == vehiculo.Placa).first()
    
    if db_vehiculo:
        # El vehículo existe. Si este conductor no está entre sus dueños, lo agregamos.
        if current_user.conductor not in db_vehiculo.conductores:
            import datetime
            fecha_actual = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            asociacion = VehiculoConductor(fechareg=fecha_actual, conductor_id=current_user.conductor.IdUsuario, vehiculo_id=db_vehiculo.Id)
            db.add(asociacion)
            db.commit()
            db.refresh(db_vehiculo)
        return db_vehiculo

    # Si no existe, creamos el vehículo
    # model_dump() es para Pydantic V2. Si arroja error en el futuro, cámbialo por dict()
    nuevo_vehiculo_data = vehiculo.model_dump() if hasattr(vehiculo, 'model_dump') else vehiculo.dict()
    db_vehiculo = Vehiculo(**nuevo_vehiculo_data)
    db.add(db_vehiculo)
    db.commit()
    db.refresh(db_vehiculo)
    
    # Y lo vinculamos al conductor actual usando el modelo asociativo
    import datetime
    fecha_actual = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    asociacion = VehiculoConductor(fechareg=fecha_actual, conductor_id=current_user.conductor.IdUsuario, vehiculo_id=db_vehiculo.Id)
    db.add(asociacion)
    db.commit()
    db.refresh(db_vehiculo)
    
    return db_vehiculo

@router.get("/mis-vehiculos", response_model=List[VehiculoSchema])
def obtener_mis_vehiculos(
    db: Session = Depends(get_db), 
    current_user: Usuario = Depends(get_current_user)
):
    # Devolveremos la lista de vehículos vinculados al conductor actual
    if not current_user.conductor:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Debe tener un perfil de conductor para ver sus vehículos"
        )
        
    return current_user.conductor.vehiculos
