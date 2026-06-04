from src.core.database import get_db
from src.modules.iam.dependencies import get_current_user, require_admin
from src.core.security import create_access_token, get_password_hash, verify_password, ACCESS_TOKEN_EXPIRE_MINUTES, SECRET_KEY, ALGORITHM
from src.shared.bitacora_util import registrar_bitacora
from src.shared.email_util import enviar_email_reset
from src.modules.iam.models import Permiso, Rol, Usuario
from src.modules.catalog.models import Administrador, Conductor, Taller
from src.modules.catalog.schemas import ConductorRegistro, TallerRegistro
from src.modules.iam.schemas import (
    MensajeResponse, PasswordReset, PasswordResetRequest, Token, UsuarioCreate,
    Rol as RolSchema, Usuario as UsuarioSchema, UsuarioUpdate,
    Permiso as PermisoSchema, RolCreate, FCMTokenUpdate
)

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import Annotated, List


router = APIRouter(tags=["IAM - Seguridad y Accesos"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# ─── AUTHENTICATION ──────────────────────────────────────────────────────────

auth_router = APIRouter(prefix="/auth", tags=["Authentication"])

@auth_router.post("/login", response_model=Token)
def login_for_access_token(request: Request, form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: Session = Depends(get_db)):
    user = db.query(Usuario).filter(Usuario.Correo == form_data.username).first()
    
    if not user or not verify_password(form_data.password, user.Password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo electrónico o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.Correo, "tenant_id": user.tenant_id}, expires_delta=access_token_expires
    )
    role_name = user.rol.Nombre if user.rol else None
    permisos_list = [p.Nombre for p in user.rol.permisos] if user.rol and user.rol.permisos else []
    registrar_bitacora(
        db, user.Id, "Inicio de Sesión",
        f"El usuario {user.Correo} inició sesión",
        ip=request.client.host if request.client else "0.0.0.0"
    )

    return {
        "access_token": access_token, 
        "token_type": "bearer", 
        "role": role_name,
        "permisos": permisos_list,
        "tenant_id": user.tenant_id
    }

@auth_router.post("/registrar", response_model=dict)
def register_user(usuario: UsuarioCreate, db: Session = Depends(get_db)):
    rol = db.query(Rol).filter(Rol.Id == usuario.IdRol).first()
    if not rol:
        rol = Rol(Id=usuario.IdRol, Nombre="Rol Generado Auto")
        db.add(rol)
        db.commit()
    
    db_user = db.query(Usuario).filter(Usuario.Correo == usuario.Correo).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Este correo ya está registrado")
    
    hashed_password = get_password_hash(usuario.Password)
    new_user = Usuario(Correo=usuario.Correo, Password=hashed_password, IdRol=usuario.IdRol)
    
    db.add(new_user)
    db.commit()
    return {"message": "Usuario registrado exitosamente"}

@auth_router.post("/registrar-conductor", response_model=dict)
def register_conductor(request: Request, conductor_data: ConductorRegistro, db: Session = Depends(get_db)):
    rol = db.query(Rol).filter(Rol.Nombre == "Conductor").first()
    if not rol:
        rol = Rol(Nombre="Conductor")
        db.add(rol)
        db.commit()
        db.refresh(rol)

    if db.query(Usuario).filter(Usuario.Correo == conductor_data.Correo).first():
        raise HTTPException(status_code=400, detail="Este correo ya está registrado en el sistema")

    hashed_pass = get_password_hash(conductor_data.Password)
    new_user = Usuario(Correo=conductor_data.Correo, Password=hashed_pass, IdRol=rol.Id)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    nuevo_conductor = Conductor(
        IdUsuario=new_user.Id,
        CI=conductor_data.CI,
        Nombre=conductor_data.Nombre,
        Apellidos=conductor_data.Apellidos,
        Fechanac=conductor_data.Fechanac
    )
    db.add(nuevo_conductor)
    db.commit()

    registrar_bitacora(
        db, new_user.Id, "Registro",
        f"Nuevo conductor registrado: {conductor_data.Nombre} {conductor_data.Apellidos}",
        ip=request.client.host if request.client else "0.0.0.0"
    )
    return {"message": "Conductor registrado exitosamente"}

@auth_router.post("/registrar-taller", response_model=dict)
def register_taller(request: Request, taller_data: TallerRegistro, db: Session = Depends(get_db)):
    rol = db.query(Rol).filter(Rol.Nombre == "Taller").first()
    if not rol:
        rol = Rol(Nombre="Taller")
        permiso = db.query(Permiso).filter(Permiso.Nombre == "Gestionar Mecanicos").first()
        if permiso:
            rol.permisos.append(permiso)
        db.add(rol)
        db.commit()
        db.refresh(rol)

    if db.query(Usuario).filter(Usuario.Correo == taller_data.Correo).first():
        raise HTTPException(status_code=400, detail="Este correo ya está registrado por otra cuenta")

    hashed_pass = get_password_hash(taller_data.Password)
    new_user = Usuario(Correo=taller_data.Correo, Password=hashed_pass, IdRol=rol.Id)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    nuevo_taller = Taller(
        IdUsuario=new_user.Id,
        Nombre=taller_data.Nombre,
        Direccion=taller_data.Direccion,
        Coordenadas=taller_data.Coordenadas,
        Cap=taller_data.Cap if taller_data.Cap is not None else 0,
        Capmax=taller_data.Capmax if taller_data.Capmax is not None else 10
    )
    db.add(nuevo_taller)
    db.commit()

    registrar_bitacora(
        db, new_user.Id, "Registro",
        f"Nuevo taller registrado: {taller_data.Nombre}",
        ip=request.client.host if request.client else "0.0.0.0"
    )
    
    return {"message": "Taller registrado exitosamente. Ahora puede iniciar sesión."}


# --- Recuperación de Contraseña ---

@auth_router.post("/solicitar-reset", response_model=MensajeResponse)
def solicitar_reset_password(payload: PasswordResetRequest, db: Session = Depends(get_db)):
    """Envía un correo con un link para restablecer la contraseña."""
    user = db.query(Usuario).filter(Usuario.Correo == payload.correo).first()

    if not user:
        return {"message": "Si el correo está registrado, recibirás un enlace para restablecer tu contraseña."}

    reset_token = create_access_token(
        data={"sub": user.Correo, "type": "password_reset"},
        expires_delta=timedelta(minutes=30)
    )

    try:
                enviar_email_reset(user.Correo, reset_token)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al enviar el correo: {str(e)}"
        )

    return {"message": "Si el correo está registrado, recibirás un enlace para restablecer tu contraseña."}


@auth_router.post("/restablecer-password", response_model=MensajeResponse)
def restablecer_password(payload: PasswordReset, db: Session = Depends(get_db)):
    """Restablece la contraseña usando el token enviado por correo."""
    from jose import JWTError, jwt
    
    try:
        token_data = jwt.decode(payload.token, SECRET_KEY, algorithms=[ALGORITHM])
        correo = token_data.get("sub")
        token_type = token_data.get("type")

        if not correo or token_type != "password_reset":
            raise HTTPException(status_code=400, detail="Token inválido")

    except JWTError:
        raise HTTPException(status_code=400, detail="Token inválido o expirado")

    user = db.query(Usuario).filter(Usuario.Correo == correo).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    user.Password = get_password_hash(payload.nueva_password)
    db.commit()

    return {"message": "Contraseña actualizada exitosamente. Ya puedes iniciar sesión."}


# ─── USERS (CRUD) ────────────────────────────────────────────────────────────

users_router = APIRouter(prefix="/users", tags=["Usuarios"])

@users_router.get("/", response_model=List[UsuarioSchema])
def get_users(
    db: Session = Depends(get_db), 
    current_user: Usuario = Depends(require_admin),
    skip: int = 0, 
    limit: int = 100
):
    query = db.query(Usuario)
    if current_user.tenant_id is not None:
        query = query.filter(Usuario.tenant_id == current_user.tenant_id)
    users = query.offset(skip).limit(limit).all()
    return users

@users_router.get("/roles", response_model=List[RolSchema])
def get_roles_for_users(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    roles = db.query(Rol).all()
    return roles

@users_router.post("/", response_model=UsuarioSchema, status_code=status.HTTP_201_CREATED)
def create_user(
    request: Request,
    user_data: UsuarioCreate, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """Crea un nuevo usuario (solo accesible por Administradores)."""
    if db.query(Usuario).filter(Usuario.Correo == user_data.Correo).first():
        raise HTTPException(status_code=400, detail="Este correo ya está registrado")
    
    rol = db.query(Rol).filter(Rol.Id == user_data.IdRol).first()
    if not rol:
        raise HTTPException(status_code=400, detail="El rol especificado no existe")
    
    hashed_password = get_password_hash(user_data.Password)
    new_user = Usuario(
        Correo=user_data.Correo, 
        Password=hashed_password, 
        IdRol=user_data.IdRol,
        tenant_id=current_user.tenant_id
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    registrar_bitacora(
        db, current_user.Id, "Crear Usuario",
        f"Creó el usuario {new_user.Correo} con rol {rol.Nombre}",
        ip=request.client.host if request.client else "0.0.0.0"
    )
    return new_user

@users_router.put("/{user_id}", response_model=UsuarioSchema)
def update_user(
    request: Request,
    user_id: int, 
    user_data: UsuarioUpdate, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    query = db.query(Usuario).filter(Usuario.Id == user_id)
    if current_user.tenant_id is not None:
        query = query.filter(Usuario.tenant_id == current_user.tenant_id)
    db_user = query.first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    if user_data.Correo and user_data.Correo != db_user.Correo:
        if db.query(Usuario).filter(Usuario.Correo == user_data.Correo).first():
            raise HTTPException(status_code=400, detail="El correo ya se encuentra en uso por otro usuario")
        db_user.Correo = user_data.Correo
        
    if user_data.Password:
        db_user.Password = get_password_hash(user_data.Password)
        
    if user_data.IdRol is not None:
        rol = db.query(Rol).filter(Rol.Id == user_data.IdRol).first()
        if not rol:
            raise HTTPException(status_code=400, detail="El rol especificado no existe")
        db_user.IdRol = user_data.IdRol
        
    db.commit()
    db.refresh(db_user)

    registrar_bitacora(
        db, current_user.Id, "Editar Usuario",
        f"Editó al usuario #{user_id} ({db_user.Correo})",
        ip=request.client.host if request.client else "0.0.0.0"
    )
    return db_user

@users_router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    request: Request,
    user_id: int, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    query = db.query(Usuario).filter(Usuario.Id == user_id)
    if current_user.tenant_id is not None:
        query = query.filter(Usuario.tenant_id == current_user.tenant_id)
    user = query.first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    if user.Id == current_user.Id:
        raise HTTPException(status_code=400, detail="No puedes eliminar tu propia cuenta de administrador")
    
    correo_eliminado = user.Correo

    db.query(Administrador).filter(Administrador.IdUsuario == user_id).delete()
    db.query(Conductor).filter(Conductor.IdUsuario == user_id).delete()
    db.query(Taller).filter(Taller.IdUsuario == user_id).delete()

    db.delete(user)
    db.commit()

    registrar_bitacora(
        db, current_user.Id, "Eliminar Usuario",
        f"Eliminó al usuario #{user_id} ({correo_eliminado})",
        ip=request.client.host if request.client else "0.0.0.0"
    )
    return None


# ─── ROLES & PERMISOS ────────────────────────────────────────────────────────

roles_router = APIRouter(prefix="/roles", tags=["Roles y Permisos"])

@roles_router.get("/", response_model=List[RolSchema])
def get_roles(db: Session = Depends(get_db)):
    """Extrae todos los roles junto con sus permisos asignados."""
    roles = db.query(Rol).all()
    return roles

@roles_router.post("/", response_model=RolSchema, status_code=status.HTTP_201_CREATED)
def create_role(request: Request, role_data: RolCreate, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    if db.query(Rol).filter(Rol.Nombre == role_data.Nombre).first():
        raise HTTPException(status_code=400, detail="Ya existe un rol con ese nombre")
        
    nuevo_rol = Rol(Nombre=role_data.Nombre)
    db.add(nuevo_rol)
    db.commit()
    db.refresh(nuevo_rol)

    registrar_bitacora(
        db, current_user.Id, "Crear Rol",
        f"Creó el rol '{nuevo_rol.Nombre}'",
        ip=request.client.host if request.client else "0.0.0.0"
    )
    return nuevo_rol

@roles_router.put("/{role_id}", response_model=RolSchema)
def update_role(request: Request, role_id: int, role_data: RolCreate, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    db_rol = db.query(Rol).filter(Rol.Id == role_id).first()
    if not db_rol:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
        
    if role_data.Nombre != db_rol.Nombre:
        if db.query(Rol).filter(Rol.Nombre == role_data.Nombre).first():
            raise HTTPException(status_code=400, detail="Ya existe un rol con ese nombre")
        db_rol.Nombre = role_data.Nombre
        db.commit()
        db.refresh(db_rol)
        
    registrar_bitacora(
        db, current_user.Id, "Editar Rol",
        f"Editó el rol #{role_id} a '{db_rol.Nombre}'",
        ip=request.client.host if request.client else "0.0.0.0"
    )
    return db_rol

@roles_router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_role(request: Request, role_id: int, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    db_rol = db.query(Rol).filter(Rol.Id == role_id).first()
    if not db_rol:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
        
    usuarios_activos = db.query(Usuario).filter(Usuario.IdRol == role_id).count()
    if usuarios_activos > 0:
        raise HTTPException(
            status_code=400, 
            detail=f"Imposible eliminar. El rol está actualmente asignado a {usuarios_activos} usuario(s)."
        )
        
    nombre_eliminado = db_rol.Nombre
    db_rol.permisos.clear()
    
    db.delete(db_rol)
    db.commit()

    registrar_bitacora(
        db, current_user.Id, "Eliminar Rol",
        f"Eliminó el rol '{nombre_eliminado}'",
        ip=request.client.host if request.client else "0.0.0.0"
    )
    return None

@roles_router.get("/permisos/todos", response_model=List[PermisoSchema])
def get_all_permisos(db: Session = Depends(get_db)):
    return db.query(Permiso).all()

@roles_router.post("/{role_id}/permisos/{permiso_id}", status_code=status.HTTP_201_CREATED)
def assign_permiso_to_role(request: Request, role_id: int, permiso_id: int, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    db_rol = db.query(Rol).filter(Rol.Id == role_id).first()
    if not db_rol:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
        
    db_perm = db.query(Permiso).filter(Permiso.Id == permiso_id).first()
    if not db_perm:
        raise HTTPException(status_code=404, detail="Permiso no encontrado")
        
    if db_perm not in db_rol.permisos:
        db_rol.permisos.append(db_perm)
        db.commit()

    registrar_bitacora(
        db, current_user.Id, "Asignar Permiso",
        f"Asignó permiso '{db_perm.Nombre}' al rol '{db_rol.Nombre}'",
        ip=request.client.host if request.client else "0.0.0.0"
    )
    return {"message": "Permiso asignado"}

@roles_router.delete("/{role_id}/permisos/{permiso_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_permiso_from_role(request: Request, role_id: int, permiso_id: int, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    db_rol = db.query(Rol).filter(Rol.Id == role_id).first()
    if not db_rol:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
        
    db_perm = db.query(Permiso).filter(Permiso.Id == permiso_id).first()
    if not db_perm:
        raise HTTPException(status_code=404, detail="Permiso no encontrado")
        
    if db_perm in db_rol.permisos:
        db_rol.permisos.remove(db_perm)
        db.commit()

    registrar_bitacora(
        db, current_user.Id, "Revocar Permiso",
        f"Revocó permiso '{db_perm.Nombre}' del rol '{db_rol.Nombre}'",
        ip=request.client.host if request.client else "0.0.0.0"
    )
    return None
