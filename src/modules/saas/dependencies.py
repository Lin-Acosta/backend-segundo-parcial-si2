from fastapi import Depends, HTTPException, status
from src.modules.iam.dependencies import get_current_user
from src.modules.iam.models import Usuario
from src.modules.saas.models import Tenant
from src.core.database import get_db
from sqlalchemy.orm import Session


def get_current_tenant_id(current_user: Usuario = Depends(get_current_user)) -> int:
    """Extrae el tenant_id del usuario autenticado. Lanza 403 si no tiene tenant."""
    if current_user.tenant_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El usuario no está asociado a ningún tenant."
        )
    return current_user.tenant_id


def require_active_subscription(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Verifica que el tenant del usuario tenga una suscripción activa."""
    if current_user.tenant_id is None:
        return  # Super admin sin tenant puede pasar

    tenant = db.query(Tenant).filter(Tenant.Id == current_user.tenant_id).first()
    if not tenant or tenant.SuscripcionActiva != 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="La suscripción del tenant no está activa. Contacte al administrador."
        )
    return tenant


def require_super_admin(current_user: Usuario = Depends(get_current_user)):
    """Solo permite acceso a usuarios sin tenant_id (administradores de plataforma)."""
    if current_user.tenant_id is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso restringido a administradores de plataforma."
        )
    if not current_user.rol or current_user.rol.Nombre != "Administrador":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requieren permisos de Administrador de plataforma."
        )
    return current_user
