from pydantic import BaseModel
from typing import List, Optional
from datetime import date
from pydantic import BaseModel, EmailStr, constr, validator

lista_categorias=["gratis","deporte","entretenimiento","academico","hogar","online","otros"]

class UsuarioBase(BaseModel):
    username: str

class UsuarioCreate(BaseModel):
    username: constr(strip_whitespace=True, min_length=1, max_length=50)
    contraseña: constr(min_length=6, max_length=100)
    nombre_apellido: constr(min_length=1, max_length=100)
    edad: int
    latitud: float
    longitud: float
    mail: EmailStr
    telefono: constr(min_length=9, max_length=9)
    sexo: constr(max_length=1)
    descripcion: str
    suscripciones: str

    @validator('sexo')
    def validate_sexo(cls, v):
        if v not in ('M', 'F', 'O'):
            raise ValueError('Invalid sexo value')
        return v.upper()
    
class UsuarioDetails(UsuarioBase):
    nombre_apellido: str
    edad: int
    latitud: float
    longitud: float
    mail: str
    telefono: str
    sexo: str
    descripcion: str
    suscripciones: str

    class Config:
        from_attributes = True

class AuthForm(BaseModel):
    username: str
    password: str



class UsuarioResponse(BaseModel):
    username: str

    class Config:
        from_attributes = True
        
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    id: str | None = None

class TokenConUsuario(BaseModel):
    access_token: str
    refresh_token: str 
    token_type: str


class FirebaseClientToken(BaseModel):
    fcm_client_token: str



class PeticionServicioCreate(BaseModel):
    titulo: str
    descripcion: str
    precio: float
    fecha: Optional[date] = date.today()  
    latitud: float
    longitud: float
    categorias: str

    @validator('categorias')
    def validate_categoria(cls, v):
        categories = [category.strip() for category in v.split(',')]
        if not all(category in lista_categorias for category in categories):
            raise ValueError("Categorías no válidas")
        return v

class PeticionServicioDetails(BaseModel):
    id: int
    username: str
    titulo: str
    descripcion: str
    precio: float
    fecha: date
    latitud: float
    longitud: float
    categorias: str

    class Config:
        from_attributes = True

class BusquedaPeticionServicio(BaseModel):
    texto_busqueda: Optional[str] = None
    categorias: Optional[str] = None
    distancia_maxima: Optional[float] = None  
    precio_minimo: Optional[float] = None
    precio_maximo: Optional[float] = None
    latitud: Optional[float] = None
    longitud: Optional[float] = None
    @validator('categorias')
    def validate_categoria(cls, v):
        categories = [category.strip() for category in v.split(',')]
        if not all(category in lista_categorias for category in categories):
            raise ValueError("Categorías no válidas")
        return v

# Esquema para crear un acuerdo/deal
class DealCreate(BaseModel):
    id_peticion: int
    

class PeticionServicioResponse(BaseModel):
    id: int
    username: str
    titulo: str
    descripcion: str
    precio: float
    fecha: date  # Asumiendo que la fecha es una cadena para simplificar
    latitud: Optional[float] = None
    longitud: Optional[float] = None
    categorias: str

    class Config:
        orm_mode = True