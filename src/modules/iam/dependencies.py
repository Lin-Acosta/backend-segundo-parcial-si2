from src.core.database import get_db
from src.core.security import SECRET_KEY, ALGORITHM
from src.modules.iam.models import Usuario
from src.modules.iam.schemas import TokenData
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        correo: str = payload.get("sub")
        tenant_id: int = payload.get("tenant_id")
        if correo is None:
            raise credentials_exception
        token_data = TokenData(correo=correo, tenant_id=tenant_id)
    except JWTError:
        raise credentials_exception
    
    user = db.query(Usuario).filter(Usuario.Correo == token_data.correo).first()
    if user is None:
        raise credentials_exception
    return user


def require_admin(current_user: Usuario = Depends(get_current_user)):
    """Dependencia que verifica que el usuario actual sea Administrador."""
    if not current_user.rol or current_user.rol.Nombre != "Administrador":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado. Se requieren permisos de Administrador."
        )
    return current_user

from src.core.database import SessionLocal

def verify_token_ws(token: str) -> Usuario | None:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        correo: str = payload.get("sub")
        if correo is None:
            return None
    except JWTError:
        return None
    
    db = SessionLocal()
    try:
        user = db.query(Usuario).filter(Usuario.Correo == correo).first()
        return user
    finally:
        db.close()
