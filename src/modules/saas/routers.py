from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from src.core.database import get_db
from src.modules.iam.dependencies import get_current_user
from src.modules.iam.models import Usuario
from src.modules.saas.models import Tenant, PlanSaaS, Suscripcion
from src.modules.saas.schemas import (
    TenantCreate, TenantUpdate, TenantOut,
    PlanSaaSCreate, PlanSaaSOut,
    SuscripcionCreate, SuscripcionOut,
)
from src.modules.saas.dependencies import require_super_admin


router = APIRouter(
    prefix="/saas",
    tags=["SaaS Multi-Tenant"]
)


# ─── TENANTS ──────────────────────────────────────────────────────────────────

@router.get("/tenants", response_model=List[TenantOut])
def listar_tenants(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_super_admin)
):
    """Lista todos los tenants registrados en la plataforma (solo super admin)."""
    return db.query(Tenant).all()


@router.post("/tenants", response_model=TenantOut, status_code=status.HTTP_201_CREATED)
def crear_tenant(
    payload: TenantCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_super_admin)
):
    """Registra un nuevo tenant en la plataforma."""
    tenant = Tenant(
        Nombre=payload.Nombre,
        Dominio=payload.Dominio,
        LogoUrl=payload.LogoUrl,
        SuscripcionActiva=1,
        CreatedAt=datetime.utcnow()
    )
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return tenant


@router.put("/tenants/{tenant_id}", response_model=TenantOut)
def actualizar_tenant(
    tenant_id: int,
    payload: TenantUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_super_admin)
):
    """Actualiza los datos de un tenant."""
    tenant = db.query(Tenant).filter(Tenant.Id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant no encontrado")

    if payload.Nombre is not None:
        tenant.Nombre = payload.Nombre
    if payload.SuscripcionActiva is not None:
        tenant.SuscripcionActiva = payload.SuscripcionActiva
    if payload.Dominio is not None:
        tenant.Dominio = payload.Dominio
    if payload.LogoUrl is not None:
        tenant.LogoUrl = payload.LogoUrl

    db.commit()
    db.refresh(tenant)
    return tenant


@router.delete("/tenants/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_tenant(
    tenant_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_super_admin)
):
    """Elimina un tenant y todos sus datos asociados."""
    tenant = db.query(Tenant).filter(Tenant.Id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant no encontrado")
    db.delete(tenant)
    db.commit()
    return None


# ─── PLANES ───────────────────────────────────────────────────────────────────

@router.get("/planes", response_model=List[PlanSaaSOut])
def listar_planes(db: Session = Depends(get_db)):
    """Lista todos los planes SaaS disponibles (público)."""
    return db.query(PlanSaaS).filter(PlanSaaS.Activo == True).all()


@router.post("/planes", response_model=PlanSaaSOut, status_code=status.HTTP_201_CREATED)
def crear_plan(
    payload: PlanSaaSCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_super_admin)
):
    """Crea un nuevo plan SaaS."""
    plan = PlanSaaS(**payload.model_dump())
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


# ─── SUSCRIPCIONES ────────────────────────────────────────────────────────────

@router.get("/suscripciones", response_model=List[SuscripcionOut])
def listar_suscripciones(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Lista suscripciones del tenant del usuario, o todas si es super admin."""
    if current_user.tenant_id is None:
        return db.query(Suscripcion).all()
    return db.query(Suscripcion).filter(Suscripcion.tenant_id == current_user.tenant_id).all()


@router.post("/suscripciones", response_model=SuscripcionOut, status_code=status.HTTP_201_CREATED)
def crear_suscripcion(
    payload: SuscripcionCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_super_admin)
):
    """Crea una nueva suscripción para un tenant."""
    # Validar tenant y plan
    tenant = db.query(Tenant).filter(Tenant.Id == payload.tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant no encontrado")

    plan = db.query(PlanSaaS).filter(PlanSaaS.Id == payload.plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan no encontrado")

    suscripcion = Suscripcion(
        tenant_id=payload.tenant_id,
        plan_id=payload.plan_id,
        FechaInicio=datetime.utcnow(),
        Estado="Activa"
    )
    db.add(suscripcion)

    # Activar el tenant
    tenant.SuscripcionActiva = 1

    db.commit()
    db.refresh(suscripcion)
    return suscripcion
