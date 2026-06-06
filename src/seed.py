import datetime
from typing import Dict, Tuple

from src.core.database import Base, SessionLocal, engine
from src.core.security import get_password_hash

from src.modules.iam.models import Permiso, Rol, Usuario, UsuarioTenant
from src.modules.saas.models import Tenant, PlanSaaS, Suscripcion
from src.modules.catalog.models import (
    Administrador,
    Conductor,
    Mecanico,
    ServicioTaller,
    Taller,
    Vehiculo,
    VehiculoConductor,
)
from src.modules.operations.models import (
    Evidencia,
    Incidente,
    MensajeChat,
    AnalisisIA,
    Bitacora, Cotizacion, Notificacion, Pago
)


def get_or_create(db, model, defaults=None, **filters):
    instance = db.query(model).filter_by(**filters).first()
    if instance:
        return instance, False
    params = dict(filters)
    if defaults:
        params.update(defaults)
    instance = model(**params)
    db.add(instance)
    db.commit()
    db.refresh(instance)
    return instance, True


def seed_roles_and_permissions(db) -> Dict[str, Rol]:
    permisos = [
        "Ver Operaciones",
        "Ver Reportes",
        "Gestionar Mecanicos",
        "Ver Usuarios",
        "Gestionar Roles",
        "Ver Bitacora",
        "Gestionar Tenants",
        "Gestionar Planes",
        "Ver Analytics"
    ]
    permiso_objs = {}
    for nombre in permisos:
        permiso, _ = get_or_create(db, Permiso, Nombre=nombre)
        permiso_objs[nombre] = permiso

    roles = {}
    for nombre in ["Administrador", "Admin Tenant", "Taller", "Conductor", "Mecanico"]:
        rol, _ = get_or_create(db, Rol, Nombre=nombre)
        roles[nombre] = rol

    # Asignar permisos según la matriz
    
    # 1. Mecanico
    if permiso_objs["Ver Operaciones"] not in roles["Mecanico"].permisos:
        roles["Mecanico"].permisos.append(permiso_objs["Ver Operaciones"])
        
    # 2. Taller
    for p in ["Ver Operaciones", "Ver Reportes", "Gestionar Mecanicos"]:
        if permiso_objs[p] not in roles["Taller"].permisos:
            roles["Taller"].permisos.append(permiso_objs[p])

    # 3. Admin Tenant
    for p in ["Ver Operaciones", "Ver Reportes", "Gestionar Mecanicos", "Ver Usuarios", "Gestionar Roles", "Ver Bitacora", "Ver Analytics"]:
        if permiso_objs[p] not in roles["Admin Tenant"].permisos:
            roles["Admin Tenant"].permisos.append(permiso_objs[p])

    # 4. Administrador (Super Admin)
    for p in ["Ver Usuarios", "Gestionar Roles", "Ver Bitacora", "Gestionar Tenants", "Gestionar Planes", "Ver Analytics"]:
        if permiso_objs[p] not in roles["Administrador"].permisos:
            roles["Administrador"].permisos.append(permiso_objs[p])
        
    db.commit()

    return roles


def seed_planes(db):
    planes = [
        {"Nombre": "Básico", "PrecioMensual": 0, "MaxUsuarios": 5, "MaxIncidentes": 50, "Descripcion": "Plan gratuito básico.", "StripePriceId": None},
        {"Nombre": "Pro", "PrecioMensual": 2900, "MaxUsuarios": 20, "MaxIncidentes": 500, "Descripcion": "Para talleres en crecimiento.", "StripePriceId": "price_mock_pro"},
        {"Nombre": "Premium", "PrecioMensual": 9900, "MaxUsuarios": 100, "MaxIncidentes": 5000, "Descripcion": "Para redes sin límites.", "StripePriceId": "price_mock_premium"},
    ]
    for p in planes:
        get_or_create(db, PlanSaaS, **p)

    return db.query(PlanSaaS).filter(PlanSaaS.Nombre == "Básico").first()

def seed_tenants(db, plan_basico) -> Tuple[Tenant, Tenant]:
    tenant1, created1 = get_or_create(db, Tenant, Nombre="Empresa Alpha SaaS", SuscripcionActiva=1, Dominio="alpha.saas.com")
    tenant2, created2 = get_or_create(db, Tenant, Nombre="Empresa Beta SaaS", SuscripcionActiva=1, Dominio="beta.saas.com")
    
    if created1:
        s1, _ = get_or_create(db, Suscripcion, tenant_id=tenant1.Id, plan_id=plan_basico.Id, Estado="Activa")
    if created2:
        s2, _ = get_or_create(db, Suscripcion, tenant_id=tenant2.Id, plan_id=plan_basico.Id, Estado="Activa")

    return tenant1, tenant2


def seed_users(db, roles: Dict[str, Rol], tenant1: Tenant, tenant2: Tenant) -> Dict[str, Usuario]:
    users = {}

    seed_users_data = [
        {
            "key": "admin",
            "Correo": "admin@demo.local",
            "Password": "Admin123!",
            "Nombre": "Admin",
            "Apellidos": "Super",
            "CI": "0000000",
            "Fechanac": datetime.date(1980, 1, 1),
            "roles_tenants": []
        },
        {
            "key": "user1",
            "Correo": "conductor1@demo.local",
            "Password": "User123!",
            "Nombre": "Juan",
            "Apellidos": "Perez",
            "CI": "1111111",
            "Fechanac": datetime.date(1990, 1, 1),
            "roles_tenants": [] # Conductor puro global
        },
        {
            "key": "user2",
            "Correo": "conductor2@demo.local",
            "Password": "User123!",
            "Nombre": "Maria",
            "Apellidos": "Gomez",
            "CI": "2222222",
            "Fechanac": datetime.date(1992, 2, 2),
            "roles_tenants": [] # Conductor puro global
        },
        {
            "key": "user3",
            "Correo": "taller1@demo.local",
            "Password": "User123!",
            "Nombre": "Carlos",
            "Apellidos": "Taller",
            "CI": "3333333",
            "Fechanac": datetime.date(1985, 3, 3),
            "roles_tenants": [
                {"rol": roles["Taller"], "tenant": tenant1}
            ]
        },
        {
            "key": "user4",
            "Correo": "taller2@demo.local",
            "Password": "User123!",
            "Nombre": "Luis",
            "Apellidos": "Taller Dos",
            "CI": "5555555",
            "Fechanac": datetime.date(1986, 3, 3),
            "roles_tenants": [
                {"rol": roles["Taller"], "tenant": tenant2}
            ]
        },
        {
            "key": "owner1",
            "Correo": "owner1@demo.local",
            "Password": "User123!",
            "Nombre": "Laura",
            "Apellidos": "Dueña",
            "CI": "4444444",
            "Fechanac": datetime.date(1988, 4, 4),
            "roles_tenants": [
                {"rol": roles["Admin Tenant"], "tenant": tenant1}
            ]
        },
    ]

    for data in seed_users_data:
        existing = db.query(Usuario).filter(Usuario.Correo == data["Correo"]).first()
        if not existing:
            hashed = get_password_hash(data["Password"])
            user = Usuario(
                Correo=data["Correo"], 
                Password=hashed,
                Nombre=data["Nombre"],
                Apellidos=data["Apellidos"],
                CI=data["CI"],
                Fechanac=data["Fechanac"]
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            existing = user
        
        users[data["key"]] = existing

        for rt in data["roles_tenants"]:
            existing_membership = db.query(UsuarioTenant).filter(
                UsuarioTenant.usuario_id == existing.Id,
                UsuarioTenant.tenant_id == rt["tenant"].Id
            ).first()
            if not existing_membership:
                membership = UsuarioTenant(
                    usuario_id=existing.Id,
                    tenant_id=rt["tenant"].Id,
                    rol_id=rt["rol"].Id
                )
                db.add(membership)
                db.commit()

    return users


def seed_profiles(db, users: Dict[str, Usuario], tenant1: Tenant, tenant2: Tenant):
    admin = users["admin"]
    admin_profile = db.query(Administrador).filter(Administrador.IdUsuario == admin.Id).first()
    if not admin_profile:
        admin_profile = Administrador(IdUsuario=admin.Id, Usuario="admin")
        db.add(admin_profile)
        db.commit()

    owner1 = users["owner1"]
    owner1_profile = db.query(Administrador).filter(Administrador.IdUsuario == owner1.Id).first()
    if not owner1_profile:
        owner1_profile = Administrador(IdUsuario=owner1.Id, Usuario="LauraTenant")
        db.add(owner1_profile)
        db.commit()

    user1 = users["user1"]
    
    conductor1 = db.query(Conductor).filter(Conductor.IdUsuario == user1.Id).first()
    if not conductor1:
        conductor1 = Conductor(
            IdUsuario=user1.Id
        )
        db.add(conductor1)
        db.commit()
        db.refresh(conductor1)
        
    user2 = users["user2"]
        
    conductor2 = db.query(Conductor).filter(Conductor.IdUsuario == user2.Id).first()
    if not conductor2:
        conductor2 = Conductor(
            IdUsuario=user2.Id
        )
        db.add(conductor2)
        db.commit()
        db.refresh(conductor2)

    user3 = users["user3"]
    
    taller1 = db.query(Taller).filter(Taller.IdUsuario == user3.Id).first()
    if not taller1:
        taller1 = Taller(
            IdUsuario=user3.Id,
            Nombre="Taller Alpha",
            Direccion="Av. Alpha 123",
            Coordenadas="-16.5,-68.15",
            Cap=2,
            Capmax=5,
            balance=0,
            tenant_id=tenant1.Id,
        )
        db.add(taller1)
        db.commit()
        db.refresh(taller1)

    user4 = users["user4"]
    mecanico1 = db.query(Mecanico).filter(Mecanico.id == user4.Id).first()
    if not mecanico1:
        mecanico1 = Mecanico(
            id=user4.Id,
            estado="Disponible",
            taller_id=taller1.Id,
            tenant_id=tenant1.Id,
        )
        db.add(mecanico1)
        db.commit()
        
    user3 = users["user3"]
    taller2 = db.query(Taller).filter(Taller.Nombre == "Taller Beta").first()
    if not taller2:
        taller2 = Taller(
            IdUsuario=user3.Id,
            Nombre="Taller Beta",
            Direccion="Av. Beta 456",
            Coordenadas="-16.51,-68.16",
            Cap=2,
            Capmax=5,
            balance=0,
            tenant_id=tenant2.Id,
        )
        db.add(taller2)
        db.commit()
        db.refresh(taller2)
        

    servicio_t1 = db.query(ServicioTaller).filter(ServicioTaller.taller_id == taller1.Id).first()
    if not servicio_t1:
        servicio_t1 = ServicioTaller(nombre="Mantenimiento General Alpha", taller_id=taller1.Id)
        db.add(servicio_t1)
        db.commit()

    servicio_t2 = db.query(ServicioTaller).filter(ServicioTaller.taller_id == taller2.Id).first()
    if not servicio_t2:
        servicio_t2 = ServicioTaller(nombre="Mantenimiento General Beta", taller_id=taller2.Id)
        db.add(servicio_t2)
        db.commit()

    return {
        "conductor1": conductor1,
        "mecanico1": mecanico1,
        "taller1": taller1,
        "conductor2": conductor2,
        "taller2": taller2
    }


def seed_vehiculos(db, conductor1: Conductor, conductor2: Conductor, tenant1: Tenant, tenant2: Tenant):
    vehiculo1 = db.query(Vehiculo).filter(Vehiculo.Placa == "AAA-111").first()
    if not vehiculo1:
        vehiculo1 = Vehiculo(Marca="Toyota", Modelo="Yaris", Placa="AAA-111")
        db.add(vehiculo1)
        db.commit()
        db.refresh(vehiculo1)
        
    relacion1 = db.query(VehiculoConductor).filter(VehiculoConductor.conductor_id == conductor1.IdUsuario, VehiculoConductor.vehiculo_id == vehiculo1.Id).first()
    if not relacion1:
        relacion1 = VehiculoConductor(fechareg=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), conductor_id=conductor1.IdUsuario, vehiculo_id=vehiculo1.Id)
        db.add(relacion1)
        db.commit()
        db.refresh(relacion1)

    vehiculo2 = db.query(Vehiculo).filter(Vehiculo.Placa == "BBB-222").first()
    if not vehiculo2:
        vehiculo2 = Vehiculo(Marca="Nissan", Modelo="Sentra", Placa="BBB-222")
        db.add(vehiculo2)
        db.commit()
        db.refresh(vehiculo2)

    relacion2 = db.query(VehiculoConductor).filter(VehiculoConductor.conductor_id == conductor2.IdUsuario, VehiculoConductor.vehiculo_id == vehiculo2.Id).first()
    if not relacion2:
        relacion2 = VehiculoConductor(fechareg=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), conductor_id=conductor2.IdUsuario, vehiculo_id=vehiculo2.Id)
        db.add(relacion2)
        db.commit()
        db.refresh(relacion2)

    return relacion1, relacion2


def seed_incidentes(db, rel1, rel2, taller1, taller2, mecanico1, tenant1, tenant2):
    fecha_pago = "2026-05-24 12:00:00"
    
    incidente1 = db.query(Incidente).filter(Incidente.vehiculoconductor_id == rel1.id, Incidente.fecha == fecha_pago).first()
    if not incidente1:
        incidente1 = Incidente(coordenadagps="-16.5,-68.15", estado="pendiente", fecha=fecha_pago, vehiculoconductor_id=rel1.id, taller_id=taller1.Id, tenant_id=tenant1.Id)
        db.add(incidente1)
        db.commit()

    incidente2 = db.query(Incidente).filter(Incidente.vehiculoconductor_id == rel2.id, Incidente.fecha == fecha_pago).first()
    if not incidente2:
        incidente2 = Incidente(coordenadagps="-16.51,-68.16", estado="taller asignado", fecha=fecha_pago, vehiculoconductor_id=rel2.id, taller_id=taller2.Id, tenant_id=tenant2.Id)
        db.add(incidente2)
        db.commit()
        db.refresh(incidente2)
        if mecanico1 not in incidente2.mecanicos:
            incidente2.mecanicos.append(mecanico1)
            db.commit()


def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        plan_basico = seed_planes(db)
        tenant1, tenant2 = seed_tenants(db, plan_basico)
        roles = seed_roles_and_permissions(db)
        users = seed_users(db, roles, tenant1, tenant2)
        profiles = seed_profiles(db, users, tenant1, tenant2)
        rel1, rel2 = seed_vehiculos(db, profiles["conductor1"], profiles["conductor2"], tenant1, tenant2)
        seed_incidentes(db, rel1, rel2, profiles["taller1"], profiles["taller2"], profiles["mecanico1"], tenant1, tenant2)
        print("Seed completado exitosamente con 2 tenants y usuarios compartidos!")
    finally:
        db.close()


if __name__ == "__main__":
    main()
