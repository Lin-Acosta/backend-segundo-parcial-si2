from src.core.database import get_db
from src.modules.iam.dependencies import get_current_user
from src.core.security import get_password_hash
from src.shared.bitacora_util import registrar_bitacora
from src.modules.iam.models import Rol, Usuario
from src.modules.catalog.models import Mecanico, Taller, Vehiculo, VehiculoConductor, Administrador, Conductor
from src.modules.catalog.schemas import (
    MecanicoOut, MecanicoRegistro, MecanicoUpdate,
    Vehiculo as VehiculoSchema, VehiculoCreate,
    ProfileOut, ProfileUpdate, AdminProfileData, ConductorProfileData, MecanicoProfileData, TallerProfileData, UbicacionUpdate
)

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List
import datetime

# ─── VEHÍCULOS ───────────────────────────────────────────────────────────────

vehiculos_router = APIRouter(prefix="/vehiculos", tags=["Vehículos"])

@vehiculos_router.post("/", response_model=VehiculoSchema)
def registrar_vehiculo(
    vehiculo: VehiculoCreate, 
    db: Session = Depends(get_db), 
    current_user: Usuario = Depends(get_current_user)
):
    if not current_user.conductor:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Debe tener un perfil de conductor para registrar vehículos"
        )
    
    db_vehiculo = None
    if vehiculo.Placa:
        db_vehiculo = db.query(Vehiculo).filter(Vehiculo.Placa == vehiculo.Placa, Vehiculo.tenant_id == current_user.tenant_id).first()
    
    if db_vehiculo:
        if current_user.conductor not in db_vehiculo.conductores:
            fecha_actual = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            asociacion = VehiculoConductor(fechareg=fecha_actual, conductor_id=current_user.conductor.IdUsuario, vehiculo_id=db_vehiculo.Id)
            db.add(asociacion)
            db.commit()
            db.refresh(db_vehiculo)
        return db_vehiculo

    nuevo_vehiculo_data = vehiculo.model_dump() if hasattr(vehiculo, 'model_dump') else vehiculo.dict()
    nuevo_vehiculo_data["tenant_id"] = current_user.tenant_id
    db_vehiculo = Vehiculo(**nuevo_vehiculo_data)
    db.add(db_vehiculo)
    db.commit()
    db.refresh(db_vehiculo)
    
    fecha_actual = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    asociacion = VehiculoConductor(fechareg=fecha_actual, conductor_id=current_user.conductor.IdUsuario, vehiculo_id=db_vehiculo.Id)
    db.add(asociacion)
    db.commit()
    db.refresh(db_vehiculo)
    
    return db_vehiculo

@vehiculos_router.get("/mis-vehiculos", response_model=List[VehiculoSchema])
def obtener_mis_vehiculos(
    db: Session = Depends(get_db), 
    current_user: Usuario = Depends(get_current_user)
):
    if not current_user.conductor:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Debe tener un perfil de conductor para ver sus vehículos"
        )
    return current_user.conductor.vehiculos


# ─── MECÁNICOS ───────────────────────────────────────────────────────────────

mecanicos_router = APIRouter(prefix="/mecanicos", tags=["Mecanicos"])

@mecanicos_router.get("/", response_model=List[MecanicoOut])
def get_mecanicos_by_taller(db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    taller = db.query(Taller).filter(Taller.IdUsuario == current_user.Id).first()
    
    if taller:
        mecanicos = db.query(Mecanico).filter(Mecanico.taller_id == taller.Id).all()
        return mecanicos
    elif current_user.rol and current_user.rol.Nombre == 'Administrador':
        if current_user.tenant_id is None:
            return db.query(Mecanico).all()
        return db.query(Mecanico).filter(Mecanico.tenant_id == current_user.tenant_id).all()
    else:
        raise HTTPException(status_code=403, detail="No autorizado para visualizar mecánicos")

@mecanicos_router.post("/", response_model=MecanicoOut, status_code=status.HTTP_201_CREATED)
def create_mecanico(request: Request, mecanico_data: MecanicoRegistro, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    taller = db.query(Taller).filter(Taller.IdUsuario == current_user.Id).first()
    if not taller:
        raise HTTPException(status_code=403, detail="Debe ser un Taller registrado para crear mecánicos")

    if db.query(Usuario).filter(Usuario.Correo == mecanico_data.correo).first():
        raise HTTPException(status_code=400, detail="Este correo ya está registrado en el sistema")

    rol = db.query(Rol).filter(Rol.Nombre == 'Mecanico').first()
    if not rol:
        rol = Rol(Nombre='Mecanico')
        db.add(rol)
        db.commit()
        db.refresh(rol)

    hashed_pass = get_password_hash(mecanico_data.password)
    new_user = Usuario(Correo=mecanico_data.correo, Password=hashed_pass, IdRol=rol.Id, tenant_id=current_user.tenant_id)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    nuevo_mecanico = Mecanico(
        id=new_user.Id,
        ci=mecanico_data.ci,
        extci=mecanico_data.extci,
        nombre=mecanico_data.nombre,
        apellidos=mecanico_data.apellidos,
        fechanac=mecanico_data.fechanac,
        taller_id=taller.Id,
        tenant_id=current_user.tenant_id
    )
    db.add(nuevo_mecanico)
    db.commit()
    db.refresh(nuevo_mecanico)

    registrar_bitacora(
        db, current_user.Id, "Crear Mecánico",
        f"Registró al mecánico {mecanico_data.nombre} {mecanico_data.apellidos}",
        ip=request.client.host if request.client else "0.0.0.0"
    )
    return nuevo_mecanico

@mecanicos_router.put("/{mecanico_id}", response_model=MecanicoOut)
def update_mecanico(request: Request, mecanico_id: int, m_update: MecanicoUpdate, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    mecanico = db.query(Mecanico).filter(Mecanico.id == mecanico_id).first()
    if not mecanico:
        raise HTTPException(status_code=404, detail="Mecánico no encontrado")

    taller = db.query(Taller).filter(Taller.IdUsuario == current_user.Id).first()
    is_owner_taller = taller and mecanico.taller_id == taller.Id
    is_admin = current_user.rol and current_user.rol.Nombre == 'Administrador'
    is_self = hasattr(current_user, 'mecanico') and current_user.mecanico and current_user.mecanico.id == mecanico_id

    if not (is_owner_taller or is_admin or is_self):
        raise HTTPException(status_code=403, detail="No puedes editar mecánicos de otros talleres")

    if m_update.nombre is not None:
        mecanico.nombre = m_update.nombre
    if m_update.apellidos is not None:
        mecanico.apellidos = m_update.apellidos
    if m_update.ci is not None:
        mecanico.ci = m_update.ci
    if m_update.extci is not None:
        mecanico.extci = m_update.extci
    if m_update.fechanac is not None:
        mecanico.fechanac = m_update.fechanac
    if m_update.estado is not None:
        mecanico.estado = m_update.estado

    db.commit()
    db.refresh(mecanico)

    registrar_bitacora(
        db, current_user.Id, "Editar Mecánico",
        f"Editó al mecánico #{mecanico_id}",
        ip=request.client.host if request.client else "0.0.0.0"
    )
    return mecanico

@mecanicos_router.delete("/{mecanico_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_mecanico(request: Request, mecanico_id: int, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    mecanico = db.query(Mecanico).filter(Mecanico.id == mecanico_id).first()
    if not mecanico:
        raise HTTPException(status_code=404, detail="Mecánico no encontrado")

    taller = db.query(Taller).filter(Taller.IdUsuario == current_user.Id).first()
    if not taller or mecanico.taller_id != taller.Id:
        if not (current_user.rol and current_user.rol.Nombre == 'Administrador'):
            raise HTTPException(status_code=403, detail="No puedes dar de baja técnicos que no te pertenecen")

    user_id = mecanico.id
    db.delete(mecanico)
    
    base_user = db.query(Usuario).filter(Usuario.Id == user_id).first()
    if base_user:
        db.delete(base_user)

    db.commit()

    registrar_bitacora(
        db, current_user.Id, "Eliminar Mecánico",
        f"Dio de baja al mecánico #{mecanico_id}",
        ip=request.client.host if request.client else "0.0.0.0"
    )
    return None


# ─── PROFILE ─────────────────────────────────────────────────────────────────

profile_router = APIRouter(prefix="/profile", tags=["Perfil de Usuario"])

@profile_router.get("/me", response_model=ProfileOut)
def get_my_profile(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    rol_nombre = current_user.rol.Nombre if current_user.rol else None

    admin_data = None
    taller_data = None
    conductor_data = None
    mecanico_data = None

    if current_user.administrador:
        admin_data = AdminProfileData(Usuario=current_user.administrador.Usuario)

    if current_user.talleres and len(current_user.talleres) > 0:
        t = current_user.talleres[0]
        taller_data = TallerProfileData(
            Id=t.Id,
            Nombre=t.Nombre,
            Direccion=t.Direccion,
            Coordenadas=t.Coordenadas,
            Cap=t.Cap,
            Capmax=t.Capmax,
            balance=t.balance
        )

    if current_user.conductor:
        conductor_data = ConductorProfileData(
            CI=current_user.conductor.CI,
            Nombre=current_user.conductor.Nombre,
            Apellidos=current_user.conductor.Apellidos,
            Fechanac=current_user.conductor.Fechanac
        )

    if current_user.mecanico:
        mecanico_data = MecanicoProfileData(
            id=current_user.mecanico.id,
            ci=current_user.mecanico.ci,
            nombre=current_user.mecanico.nombre,
            apellidos=current_user.mecanico.apellidos,
            estado=current_user.mecanico.estado
        )

    return ProfileOut(
        Id=current_user.Id,
        Correo=current_user.Correo,
        rol_nombre=rol_nombre,
        administrador=admin_data,
        taller=taller_data,
        conductor=conductor_data,
        mecanico=mecanico_data
    )

@profile_router.put("/me", response_model=ProfileOut)
def update_my_profile(
    request: Request,
    profile_data: ProfileUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if profile_data.Correo and profile_data.Correo != current_user.Correo:
        existing = db.query(Usuario).filter(
            Usuario.Correo == profile_data.Correo,
            Usuario.Id != current_user.Id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Este correo ya está en uso por otro usuario")
        current_user.Correo = profile_data.Correo

    if profile_data.Password:
        current_user.Password = get_password_hash(profile_data.Password)

    if current_user.administrador and profile_data.admin_usuario is not None:
        current_user.administrador.Usuario = profile_data.admin_usuario

    if current_user.talleres and len(current_user.talleres) > 0:
        t = current_user.talleres[0]
        if profile_data.taller_nombre is not None:
            t.Nombre = profile_data.taller_nombre
        if profile_data.taller_direccion is not None:
            t.Direccion = profile_data.taller_direccion
        if profile_data.taller_coordenadas is not None:
            t.Coordenadas = profile_data.taller_coordenadas
        if profile_data.taller_cap is not None:
            t.Cap = profile_data.taller_cap
        if profile_data.taller_capmax is not None:
            t.Capmax = profile_data.taller_capmax

    if current_user.conductor:
        if profile_data.conductor_ci is not None:
            current_user.conductor.CI = profile_data.conductor_ci
        if profile_data.conductor_nombre is not None:
            current_user.conductor.Nombre = profile_data.conductor_nombre
        if profile_data.conductor_apellidos is not None:
            current_user.conductor.Apellidos = profile_data.conductor_apellidos
        if profile_data.conductor_fechanac is not None:
            current_user.conductor.Fechanac = profile_data.conductor_fechanac

    if current_user.mecanico:
        if profile_data.mecanico_estado is not None:
            current_user.mecanico.estado = profile_data.mecanico_estado

    db.commit()
    db.refresh(current_user)

    registrar_bitacora(
        db, current_user.Id, "Editar Perfil",
        f"El usuario {current_user.Correo} actualizó su perfil",
        ip=request.client.host if request.client else "0.0.0.0"
    )

    return get_my_profile(db=db, current_user=current_user)

@profile_router.put("/me/ubicacion", response_model=ProfileOut)
def update_ubicacion_taller(
    request: Request,
    ubicacion: UbicacionUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if not current_user.talleres or len(current_user.talleres) == 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo usuarios con perfil de Taller pueden actualizar la ubicación"
        )

    taller = current_user.talleres[0]
    taller.Coordenadas = ubicacion.Coordenadas
    if ubicacion.Direccion is not None:
        taller.Direccion = ubicacion.Direccion

    db.commit()
    db.refresh(current_user)

    registrar_bitacora(
        db, current_user.Id, "Actualizar Ubicación",
        f"El taller '{taller.Nombre}' actualizó su ubicación a {ubicacion.Coordenadas}",
        ip=request.client.host if request.client else "0.0.0.0"
    )

    return get_my_profile(db=db, current_user=current_user)
