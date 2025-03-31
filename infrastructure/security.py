# infrastructure/security.py
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from infrastructure.settings import CLAVE_SECRETA, ALGORITMO_JWT, TIEMPO_EXPIRACION_TOKEN
from infrastructure.database import get_db
from domain.entities import Usuario

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/admin/usuarios/login")

TIEMPO_EXPIRACION_REFRESH_TOKEN = 7 * 24 * 60

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if not expires_delta:
        expires_delta = timedelta(minutes=int(TIEMPO_EXPIRACION_TOKEN))
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, CLAVE_SECRETA, algorithm=ALGORITMO_JWT)

def create_refresh_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if not expires_delta:
        expires_delta = timedelta(minutes=TIEMPO_EXPIRACION_REFRESH_TOKEN)
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, CLAVE_SECRETA, algorithm=ALGORITMO_JWT)

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    from infrastructure.users_repository import SQLAlchemyUSERS
    try:
        payload = jwt.decode(token, CLAVE_SECRETA, algorithms=[ALGORITMO_JWT])
        username: str = payload.get("sub")
        token_type: str = payload.get("type")
        if not username or token_type != "access":
            raise HTTPException(status_code=401, detail="Credenciales inválidas o token no válido")
        usuario_service = SQLAlchemyUSERS(db)
        usuario = usuario_service.get_usuario_by_username(username)
        if not usuario or usuario.Anulado:
            raise HTTPException(status_code=401, detail="Usuario no encontrado o anulado")
        return usuario
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")

def verify_refresh_token(token: str, db: Session = Depends(get_db)):
    from infrastructure.users_repository import SQLAlchemyUSERS
    try:
        payload = jwt.decode(token, CLAVE_SECRETA, algorithms=[ALGORITMO_JWT])
        username: str = payload.get("sub")
        token_type: str = payload.get("type")
        if not username or token_type != "refresh":
            raise HTTPException(status_code=401, detail="Refresh token inválido")
        usuario_service = SQLAlchemyUSERS(db)
        usuario = usuario_service.get_usuario_by_username(username)
        if not usuario or usuario.Anulado:
            raise HTTPException(status_code=401, detail="Usuario no encontrado o anulado")
        return usuario
    except JWTError:
        raise HTTPException(status_code=401, detail="Refresh token inválido o expirado")

def require_role(role: str):
    def role_checker(usuario: Usuario = Depends(get_current_user)):
        role_names = [r.Nombre for r in usuario.roles]
        if role not in role_names:
            raise HTTPException(status_code=403, detail=f"Se requiere rol '{role}'")
        return usuario
    return role_checker