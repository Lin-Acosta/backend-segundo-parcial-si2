from src.core.database import get_db
from src.shared.dependencies import get_current_user
from src.modules.actors.models import Mecanico, Taller
from src.modules.operations.models import Bitacora
from src.modules.security.models import Usuario
from src.modules.operations.schemas import BitacoraOut

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List


router = APIRouter(
    prefix="/bitacora",
    tags=["Bitacora"]
)

@router.get("/", response_model=List[BitacoraOut])
def get_bitacora(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
    skip: int = 0,
    limit: int = 200
):
    """
    Retorna las entradas de la bitácora según el rol del usuario:
    - Administrador: ve TODAS las entradas de todos los usuarios.
    - Taller: ve las suyas propias y las de sus técnicos (mecánicos).
    - Otros (Conductor, Mecánico, etc.): solo ven las suyas propias.
    """
    role_name = current_user.rol.Nombre if current_user.rol else None

    if role_name == "Administrador":
        # Admin ve todo
        entries = (
            db.query(Bitacora)
            .order_by(Bitacora.id.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
    elif role_name == "Taller":
        # Obtener el taller del usuario actual
        taller = db.query(Taller).filter(
            Taller.IdUsuario == current_user.Id
        ).first()

        # IDs a incluir: el propio usuario + todos sus mecánicos
        user_ids = [current_user.Id]
        if taller:
            mecanicos = db.query(Mecanico).filter(
                Mecanico.taller_id == taller.Id
            ).all()
            user_ids.extend([m.id for m in mecanicos])

        entries = (
            db.query(Bitacora)
            .filter(Bitacora.usuario_id.in_(user_ids))
            .order_by(Bitacora.id.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
    else:
        # Solo las propias
        entries = (
            db.query(Bitacora)
            .filter(Bitacora.usuario_id == current_user.Id)
            .order_by(Bitacora.id.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    # Enriquecer con datos del usuario
    result = []
    for entry in entries:
        usuario = db.query(Usuario).filter(Usuario.Id == entry.usuario_id).first()
        result.append(BitacoraOut(
            id=entry.id,
            accion=entry.accion,
            descripcion=entry.descripcion,
            fecha=entry.fecha,
            ip=entry.ip,
            usuario_id=entry.usuario_id,
            usuario_correo=usuario.Correo if usuario else "Eliminado",
            usuario_rol=usuario.rol.Nombre if usuario and usuario.rol else "Sin Rol"
        ))
    return result


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_bitacora_entry(
    entry_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Solo el Administrador puede eliminar entradas de la bitácora."""
    if not current_user.rol or current_user.rol.Nombre != "Administrador":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo el Administrador puede eliminar registros de la bitácora."
        )
    
    entry = db.query(Bitacora).filter(Bitacora.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Registro no encontrado")
    
    db.delete(entry)
    db.commit()
    return None
