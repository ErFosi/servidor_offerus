from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from . import crud
from sqlalchemy.orm import Session
from .database import SessionLocal
import os

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



SECRET_KEY = os.getenv("SECRET_KEY", "un_valor_por_defecto_secreto")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 10080))

pwd_context = CryptContext(
    schemes=["pbkdf2_sha256"],  # Using PBKDF2 with SHA256
    default="pbkdf2_sha256",
    pbkdf2_sha256__default_rounds=29000
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def crear_token_acceso(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(minutes=15)  # Valor por defecto, ajustable
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verificar_token_acceso(token: str, credenciales_exception):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credenciales_exception
        expiration = payload.get("exp")
        if expiration is not None:
            expiration_date = datetime.fromtimestamp(expiration)
            if datetime.utcnow() > expiration_date:
                raise credenciales_exception
        return {"username": username}
    except JWTError:
        raise credenciales_exception

def obtener_usuario_actual(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credenciales_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    username: str = verificar_token_acceso(token, credenciales_exception)["username"]
    usuario = crud.get_usuario(db, username=username)
    if usuario is None:
        raise credenciales_exception
    return usuario