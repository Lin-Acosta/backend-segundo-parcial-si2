from datetime import date
from sqlalchemy.orm import Session
from src.modules.operations.models import Bitacora
from src.modules.iam.models import Usuario


def registrar_bitacora(
    db: Session,
    usuario_id: int,
    accion: str,
    descripcion: str,
    ip: str = "0.0.0.0"
):
    """Registra una entrada en la bitácora de actividades del sistema."""
    usuario = db.query(Usuario).filter(Usuario.Id == usuario_id).first()
    tenant_id = usuario.tenant_id if usuario else None

    entrada = Bitacora(
        accion=accion,
        descripcion=descripcion,
        fecha=date.today(),
        ip=ip,
        usuario_id=usuario_id,
        tenant_id=tenant_id
    )
    db.add(entrada)
    db.commit()
