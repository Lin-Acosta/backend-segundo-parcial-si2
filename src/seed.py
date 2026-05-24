import datetime
from typing import Dict, Tuple

from src.core.database import Base, SessionLocal, engine
from src.core.security import get_password_hash

from src.modules.security.models import Permiso, Rol, Usuario
from src.modules.actors.models import (
    Administrador,
    Conductor,
    Mecanico,
    ServicioTaller,
    Taller,
    Vehiculo,
    VehiculoConductor,
)
from src.modules.emergencies.models import (
    Evidencia,
    Incidente,
    IncidenteMecanico,
    MensajeChat,
)
from src.modules.ai.models import AnalisisIA
from src.modules.operations.models import Bitacora, Cotizacion, Notificacion, Pago


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
    permisos = ["Gestionar Mecanicos"]
    permiso_objs = {}
    for nombre in permisos:
        permiso, _ = get_or_create(db, Permiso, Nombre=nombre)
        permiso_objs[nombre] = permiso

    roles = {}
    for nombre in ["Administrador", "Taller", "Conductor", "Mecanico"]:
        rol, _ = get_or_create(db, Rol, Nombre=nombre)
        roles[nombre] = rol

    # Asignar permisos basicos
    gestionar_mecanicos = permiso_objs["Gestionar Mecanicos"]
    if gestionar_mecanicos not in roles["Taller"].permisos:
        roles["Taller"].permisos.append(gestionar_mecanicos)
    if gestionar_mecanicos not in roles["Administrador"].permisos:
        roles["Administrador"].permisos.append(gestionar_mecanicos)
    db.commit()

    return roles


def seed_users(db, roles: Dict[str, Rol]) -> Dict[str, Usuario]:
    users = {}

    seed_users_data = [
        {
            "key": "admin",
            "Correo": "admin@demo.local",
            "Password": "Admin123!",
            "IdRol": roles["Administrador"].Id,
        },
        {
            "key": "taller",
            "Correo": "taller@demo.local",
            "Password": "Taller123!",
            "IdRol": roles["Taller"].Id,
        },
        {
            "key": "conductor",
            "Correo": "conductor@demo.local",
            "Password": "Conductor123!",
            "IdRol": roles["Conductor"].Id,
        },
        {
            "key": "mecanico",
            "Correo": "mecanico@demo.local",
            "Password": "Mecanico123!",
            "IdRol": roles["Mecanico"].Id,
        },
    ]

    for data in seed_users_data:
        existing = db.query(Usuario).filter(Usuario.Correo == data["Correo"]).first()
        if existing:
            users[data["key"]] = existing
            continue
        hashed = get_password_hash(data["Password"])
        user = Usuario(Correo=data["Correo"], Password=hashed, IdRol=data["IdRol"])
        db.add(user)
        db.commit()
        db.refresh(user)
        users[data["key"]] = user

    return users


def seed_profiles(db, users: Dict[str, Usuario]) -> Dict[str, Tuple]:
    # Administrador
    admin_user = users["admin"]
    admin_profile = db.query(Administrador).filter(Administrador.IdUsuario == admin_user.Id).first()
    if not admin_profile:
        admin_profile = Administrador(IdUsuario=admin_user.Id, Usuario="admin")
        db.add(admin_profile)
        db.commit()

    # Taller
    taller_user = users["taller"]
    taller = db.query(Taller).filter(Taller.IdUsuario == taller_user.Id).first()
    if not taller:
        taller = Taller(
            IdUsuario=taller_user.Id,
            Nombre="Taller Central",
            Direccion="Av. Principal 123",
            Coordenadas="-16.5,-68.15",
            Cap=2,
            Capmax=5,
            balance=0,
        )
        db.add(taller)
        db.commit()
        db.refresh(taller)

    # Conductor
    conductor_user = users["conductor"]
    conductor = db.query(Conductor).filter(Conductor.IdUsuario == conductor_user.Id).first()
    if not conductor:
        conductor = Conductor(
            IdUsuario=conductor_user.Id,
            CI="12345678",
            Nombre="Juan",
            Apellidos="Perez",
            Fechanac=datetime.date(1995, 1, 15),
        )
        db.add(conductor)
        db.commit()
        db.refresh(conductor)

    # Mecanico
    mecanico_user = users["mecanico"]
    mecanico = db.query(Mecanico).filter(Mecanico.id == mecanico_user.Id).first()
    if not mecanico:
        mecanico = Mecanico(
            id=mecanico_user.Id,
            ci=987654,
            extci="LP",
            nombre="Luis",
            apellidos="Gomez",
            fechanac=int(datetime.datetime(1990, 5, 20).timestamp() * 1000),
            estado="Disponible",
            taller_id=taller.Id,
        )
        db.add(mecanico)
        db.commit()
        db.refresh(mecanico)

    # Servicio de Taller
    servicio = db.query(ServicioTaller).filter(
        ServicioTaller.taller_id == taller.Id,
        ServicioTaller.nombre == "Mantenimiento General",
    ).first()
    if not servicio:
        servicio = ServicioTaller(nombre="Mantenimiento General", taller_id=taller.Id)
        db.add(servicio)
        db.commit()
        db.refresh(servicio)

    return {
        "admin": admin_profile,
        "taller": taller,
        "conductor": conductor,
        "mecanico": mecanico,
        "servicio": servicio,
    }


def seed_vehiculos(db, conductor: Conductor) -> VehiculoConductor:
    vehiculo = db.query(Vehiculo).filter(Vehiculo.Placa == "ABC-123").first()
    if not vehiculo:
        vehiculo = Vehiculo(
            Marca="Toyota",
            Modelo="Corolla",
            Placa="ABC-123",
            Poliza="POL-0001",
            Categoria="Sedan",
            Año=2020,
        )
        db.add(vehiculo)
        db.commit()
        db.refresh(vehiculo)

    relacion = db.query(VehiculoConductor).filter(
        VehiculoConductor.conductor_id == conductor.IdUsuario,
        VehiculoConductor.vehiculo_id == vehiculo.Id,
    ).first()
    if not relacion:
        relacion = VehiculoConductor(
            fechareg=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            conductor_id=conductor.IdUsuario,
            vehiculo_id=vehiculo.Id,
        )
        db.add(relacion)
        db.commit()
        db.refresh(relacion)

    return relacion


def seed_incidentes(db, vc: VehiculoConductor, taller: Taller, mecanico: Mecanico, conductor_user: Usuario):
    fecha_pago = "2026-05-24 12:00:00"
    incidente_pagado = db.query(Incidente).filter(
        Incidente.vehiculoconductor_id == vc.id,
        Incidente.fecha == fecha_pago,
    ).first()
    if not incidente_pagado:
        incidente_pagado = Incidente(
            coordenadagps="-16.5,-68.15",
            estado="Pagado",
            fecha=fecha_pago,
            vehiculoconductor_id=vc.id,
            taller_id=taller.Id,
        )
        db.add(incidente_pagado)
        db.commit()
        db.refresh(incidente_pagado)

    evidencia = db.query(Evidencia).filter(Evidencia.incidente_id == incidente_pagado.id).first()
    if not evidencia:
        evidencia = Evidencia(
            audio=None,
            descripcion="Auto no enciende, requiere revision",
            fotos=None,
            incidente_id=incidente_pagado.id,
        )
        db.add(evidencia)
        db.commit()

    analisis = db.query(AnalisisIA).filter(AnalisisIA.incidente_id == incidente_pagado.id).first()
    if not analisis:
        analisis = AnalisisIA(
            incidente_id=incidente_pagado.id,
            Clasificacion="Mecanico",
            NivelPrioridad="Media",
            Resumen="Posible falla de bateria",
            TranscripcionAudio=None,
            informacion_valida=True,
        )
        db.add(analisis)
        db.commit()

    if mecanico not in incidente_pagado.mecanicos:
        incidente_pagado.mecanicos.append(mecanico)
        db.commit()

    cotizacion = db.query(Cotizacion).filter(
        Cotizacion.incidente_id == incidente_pagado.id,
        Cotizacion.taller_id == taller.Id,
    ).first()
    if not cotizacion:
        cotizacion = Cotizacion(
            monto=350,
            mensaje="Cambio de bateria",
            estado="Aceptada",
            fecha_creacion=fecha_pago,
            incidente_id=incidente_pagado.id,
            taller_id=taller.Id,
        )
        db.add(cotizacion)
        db.commit()

    pago = db.query(Pago).filter(Pago.incidente_id == incidente_pagado.id).first()
    if not pago:
        pago = Pago(
            monto_total=350,
            metodo="Directo",
            estado="Completado",
            stripe_session_id=None,
            fecha=fecha_pago,
            incidente_id=incidente_pagado.id,
        )
        db.add(pago)
        db.commit()

    mensaje = db.query(MensajeChat).filter(
        MensajeChat.incidente_id == incidente_pagado.id,
        MensajeChat.contenido == "Estoy en camino al taller",
    ).first()
    if not mensaje:
        mensaje = MensajeChat(
            contenido="Estoy en camino al taller",
            fecha=fecha_pago,
            incidente_id=incidente_pagado.id,
            usuario_id=conductor_user.Id,
        )
        db.add(mensaje)
        db.commit()

    # Incidente pendiente para pruebas de solicitudes
    fecha_pendiente = "2026-05-24 12:30:00"
    incidente_pendiente = db.query(Incidente).filter(
        Incidente.vehiculoconductor_id == vc.id,
        Incidente.fecha == fecha_pendiente,
    ).first()
    if not incidente_pendiente:
        incidente_pendiente = Incidente(
            coordenadagps="-16.51,-68.14",
            estado="Reportado",
            fecha=fecha_pendiente,
            vehiculoconductor_id=vc.id,
            taller_id=None,
        )
        db.add(incidente_pendiente)
        db.commit()
        db.refresh(incidente_pendiente)

    evidencia_p = db.query(Evidencia).filter(Evidencia.incidente_id == incidente_pendiente.id).first()
    if not evidencia_p:
        evidencia_p = Evidencia(
            audio=None,
            descripcion="Pinchazo de llanta",
            fotos=None,
            incidente_id=incidente_pendiente.id,
        )
        db.add(evidencia_p)
        db.commit()

    return incidente_pagado, incidente_pendiente


def seed_ops(db, admin_user: Usuario, conductor_user: Usuario):
    bitacora = db.query(Bitacora).filter(
        Bitacora.usuario_id == admin_user.Id,
        Bitacora.accion == "Seeder",
    ).first()
    if not bitacora:
        bitacora = Bitacora(
            accion="Seeder",
            descripcion="Carga inicial de datos",
            fecha=datetime.date.today(),
            ip="127.0.0.1",
            usuario_id=admin_user.Id,
        )
        db.add(bitacora)
        db.commit()

    notificacion = db.query(Notificacion).filter(
        Notificacion.usuario_id == conductor_user.Id,
        Notificacion.titulo == "Bienvenido",
    ).first()
    if not notificacion:
        notificacion = Notificacion(
            descripcion="Cuenta lista para pruebas",
            estado="No leida",
            fecha=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            titulo="Bienvenido",
            usuario_id=conductor_user.Id,
        )
        db.add(notificacion)
        db.commit()


def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        roles = seed_roles_and_permissions(db)
        users = seed_users(db, roles)
        profiles = seed_profiles(db, users)
        vc = seed_vehiculos(db, profiles["conductor"])
        seed_incidentes(db, vc, profiles["taller"], profiles["mecanico"], users["conductor"])
        seed_ops(db, users["admin"], users["conductor"])
    finally:
        db.close()


if __name__ == "__main__":
    main()
