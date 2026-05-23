import os
import sys
from dotenv import load_dotenv

# Asegurar que el path del proyecto esté en python path para poder importar src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import SessionLocal, engine, Base
from src import models
from src.security import get_password_hash

def seed_db():
    print("Iniciando la creación de tablas (si no existen)...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        print("Insertando datos semilla...")
        
        # 1. Crear permisos por defecto
        permisos_defecto = ["Gestionar Mecanicos", "Gestionar Roles", "Ver Bitacora", "Ver Reportes"]
        db_permisos = {}
        for p_name in permisos_defecto:
            permiso = db.query(models.Permiso).filter(models.Permiso.Nombre == p_name).first()
            if not permiso:
                permiso = models.Permiso(Nombre=p_name)
                db.add(permiso)
                db.commit()
                db.refresh(permiso)
                print(f"Permiso creado: {p_name}")
            db_permisos[p_name] = permiso

        # 2. Crear roles por defecto
        roles_defecto = {
            "Administrador": ["Gestionar Roles", "Ver Bitacora", "Ver Reportes"],
            "Conductor": [],
            "Taller": ["Gestionar Mecanicos"]
        }
        
        db_roles = {}
        for r_name, p_names in roles_defecto.items():
            rol = db.query(models.Rol).filter(models.Rol.Nombre == r_name).first()
            if not rol:
                rol = models.Rol(Nombre=r_name)
                # Asignar permisos
                for p_name in p_names:
                    if p_name in db_permisos:
                        rol.permisos.append(db_permisos[p_name])
                db.add(rol)
                db.commit()
                db.refresh(rol)
                print(f"Rol creado: {r_name}")
            else:
                # Asegurar permisos correctos
                for p_name in p_names:
                    if p_name in db_permisos and db_permisos[p_name] not in rol.permisos:
                        rol.permisos.append(db_permisos[p_name])
                db.commit()
            db_roles[r_name] = rol

        # 3. Crear usuario administrador por defecto si no hay usuarios
        admin_email = "admin@emergenciavehicular.com"
        admin_user = db.query(models.Usuario).filter(models.Usuario.Correo == admin_email).first()
        if not admin_user:
            admin_rol = db_roles["Administrador"]
            hashed_pw = get_password_hash("admin123")
            
            # Crear usuario
            admin_user = models.Usuario(
                Correo=admin_email,
                Password=hashed_pw,
                IdRol=admin_rol.Id
            )
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)
            print(f"Usuario Administrador creado: {admin_email}")

            # Crear perfil de Administrador asociado
            admin_perfil = models.Administrador(
                IdUsuario=admin_user.Id,
                Usuario="Administrador"
            )
            db.add(admin_perfil)
            db.commit()
            print("Perfil de Administrador creado")
        else:
            print(f"El usuario Administrador ya existe: {admin_email}")

        print("¡Seeding completado con éxito!")
        
    except Exception as e:
        print(f"Error durante el seeding: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    load_dotenv()
    seed_db()
