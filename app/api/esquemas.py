from pydantic import BaseModel
from typing import List, Optional, Literal
from datetime import date
from pydantic import BaseModel, EmailStr, constr, validator, conint


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
    telefono: constr(pattern=r"^\d{9}$")
    sexo: constr(max_length=1)
    descripcion: constr(max_length=400)
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

class UsuarioUpdate(BaseModel):
    nombre_apellido: Optional[constr(min_length=1, max_length=100)] = None
    edad: Optional[int] = None
    latitud: Optional[float] = None
    longitud: Optional[float] = None
    mail: Optional[EmailStr] = None
    telefono: Optional[constr(pattern=r"^\d{9}$")] = None
    sexo: Optional[constr(max_length=1)] = None
    descripcion: Optional[constr(max_length=400)] = None
    suscripciones: Optional[str] = None

    @validator('sexo')
    def validate_sexo(cls, v):
        if v and v not in ('M', 'F', 'O'):
            raise ValueError('Invalid sexo value')
        return v.upper()
    
    class Config:
        from_attributes = True

class UsuarioModContraseña(BaseModel):
    contraseña: constr(min_length=6, max_length=100)
    nueva_contraseña: constr(min_length=6, max_length=100)
    
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
    peticion: bool
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
    peticion: bool
    descripcion: str
    precio: float
    fecha: date
    latitud: float
    longitud: float
    categorias: str

    class Config:
        from_attributes = True

class PeticionServicioUpdate(BaseModel):
    id: int
    titulo: Optional[str]
    descripcion: Optional[str] 
    peticion: Optional[bool] 
    precio: Optional[float] 
    fecha: Optional[date] 
    latitud: Optional[float] 
    longitud: Optional[float]
    categorias: Optional[str]

    @validator('categorias', pre=True, always=True)
    def split_and_validate_categories(cls, v):
        if v is not None:
            categories = [category.strip() for category in v.split(',')]
            if not all(category in lista_categorias for category in categories):
                raise ValueError("Una o más categorías no son válidas")
            return ','.join(categories)
        return v


class BusquedaPeticionServicio(BaseModel):
    texto_busqueda: Optional[str] = None
    categorias: Optional[str] = None
    distancia_maxima: Optional[float] = None  
    precio_minimo: Optional[float] = None
    precio_maximo: Optional[float] = None
    latitud: Optional[float] = None
    longitud: Optional[float] = None
    ordenar_por: Optional[Literal['precio_asc', 'precio_desc', 'distancia']] = None
    @validator('categorias')
    def validate_categoria(cls, v):
        if v is None or v.strip() == "":
            return v
        categories = [category.strip() for category in v.split(',')]
        if not all(category in lista_categorias for category in categories):
            raise ValueError("Categorías no válidas")
        return v


class PeticionesRequest(BaseModel):
    ids_pet: List[int]
    
class DealCreate(BaseModel):
    id_peticion: int
    
class DealAction(BaseModel):
    deal_id: int
    accept: bool  

class RateDeal(BaseModel):
    deal_id: int
    nota: conint(ge=0, le=5)  

    @validator('nota')
    def check_nota(cls, value):
        if value == -1:
            raise ValueError("La nota no puede ser -1")
        return value
class DealResponse(BaseModel):
    id: int
    nota_cliente: conint(ge=-1)  
    nota_host: conint(ge=-1)   
    username_cliente: str
    username_host: str
    id_peticion: int
    estado: str

    @validator('estado')
    def check_estado(cls, v):
        assert v in ['pendiente', 'aceptado', 'rechazado'], 'estado debe ser pendiente, aceptado o rechazado'
        return v

    class Config:
        from_attributes = True 

class NotaResponse(BaseModel):
    nota: float
    cant: int

class PeticionServicioResponse(BaseModel):
    id: int
    username: str
    titulo: str
    peticion:bool
    descripcion: str
    precio: float
    fecha: date  
    latitud: Optional[float] = None
    longitud: Optional[float] = None
    categorias: str

    class Config:
        from_attributes = True

class FavCreate(BaseModel):
    id_peticion: int
