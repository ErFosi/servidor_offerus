from passlib.context import CryptContext
from . import databaseORM
from . import esquemas
from sqlalchemy.orm import Session
from fastapi import HTTPException
import random
from sqlalchemy import func
import math
from sqlalchemy import or_

""" 
    Ajusta la ubicación original en una distancia aleatoria

    @param lat: Latitud original
    @param lon: Longitud original
    @param min_distance: Distancia mínima en metros
    @param max_distance: Distancia máxima en metros

    @return: Nueva latitud y longitud ajustadas
    """
def adjust_location(lat, lon, min_distance=100, max_distance=500):
    # Convertir distancia en grados
    earth_radius = 6371000  # radio de la Tierra en metros
    one_degree = 360 / (2 * 3.14159 * earth_radius)  # un grado en radianes
    
    # Calcular desplazamiento aleatorio en metros
    random_distance = random.randint(min_distance, max_distance)
    
    # Convertir a grados
    degree_change = random_distance * one_degree
    
    # Aplicar desplazamiento aleatorio a latitud y longitud
    new_lat = lat + random.choice([-1, 1]) * degree_change
    new_lon = lon + random.choice([-1, 1]) * degree_change
    
    return new_lat, new_lon

pwd_context = CryptContext(
    schemes=["pbkdf2_sha256"],  # Usar PBKDF2 con SHA256, un metodo mas seguro que me han recomendado en el curro
    default="pbkdf2_sha256",
    pbkdf2_sha256__default_rounds=29000, 
)

###############################################################################

################################PSWD###########################################

###############################################################################

"""
Metodo para hashear la contraseña

@params password: Contraseña en texto plano
@return: Hash de la contraseña

"""
def hash_password(password: str):
    hashed_pwd = pwd_context.hash(password)
    print(hashed_pwd)
    return hashed_pwd


"""
Metodo para verificar la contraseña

@params plain_password: Contraseña en texto plano
@params hashed_password: Hash de la contraseña

@return: True si la contraseña es correcta, False en caso contrario
"""
def verify_password(plain_password, hashed_password):
    print("Verifying password:")
    print("Plain:", plain_password)
    print("Hashed:", hashed_password)
    return pwd_context.verify(plain_password, hashed_password)



###############################################################################

################################USUARIOS#######################################

###############################################################################

"""
Metodo para obtener un usuario por su nombre de usuario

@params db: Session de la base de datos
@params usuario: Nombre de usuario

@return: Usuario encontrado
"""
def obtener_usuario_por_nombre_usuario(db: Session, usuario: str):
    return db.query(databaseORM.Usuario).filter(databaseORM.Usuario.username == usuario).first()

"""
Metodo para obtener un usuario por su nombre de usuario

@params db: Session de la base de datos
@params usuario: Nombre de usuario

@return: Usuario encontrado
"""
def get_usuario(db: Session, username: str):
    return db.query(databaseORM.Usuario).filter(databaseORM.Usuario.username== username).first()

"""
Metodo para crear un usuario

@params db: Session de la base de datos
@params usuario: Usuario a crear

@return: Usuario creado
"""
def create_user(db: Session, user: esquemas.UsuarioCreate):
    db_user = databaseORM.Usuario(
        username=user.username,
        contraseña=hash_password(user.contraseña),
        nombre_apellido=user.nombre_apellido,
        edad=user.edad,
        latitud=user.latitud,
        longitud=user.longitud,
        mail=user.mail,
        telefono=user.telefono,
        sexo=user.sexo,
        descripcion=user.descripcion,
        suscripciones=user.suscripciones
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
"""
Metodo para obtener todos los usuarios

@params db: Session de la base de datos
@params skip: Cantidad de usuarios a saltar

@return: Lista de usuarios

Metodo temporal
"""
def obtener_usuarios(db: Session, skip: int = 0, limit: int = 100):
    return db.query(databaseORM.Usuario).offset(skip).limit(limit).all()


"""
Metodo para obtener los detalles de un usuario

@params db: Session de la base de datos
@params username: Nombre de usuario

@return: Usuario encontrado

"""
def get_usuario_detalles(db: Session, username: str):
    return db.query(databaseORM.Usuario).filter(databaseORM.Usuario.username == username).first()

"""
Metodo para autenticar un usuario

@params db: Session de la base de datos
@params username: Nombre de usuario

@return: Usuario autenticado
"""
def authenticate_user(db: Session, username: str, password: str):
    user = db.query(databaseORM.Usuario).filter(databaseORM.Usuario.username == username).first()
    if not user:
        return False
    if not verify_password(password, user.contraseña):
        return False
    return user


###############################################################################

################################PETICIONES#####################################

###############################################################################

"""
Metodo para crear una petición de servicio

@params db: Session de la base de datos
@params peticion: Petición de servicio
@params username: Nombre de usuario

@return: Usuario autenticado
"""


def create_peticion_servicio(db: Session, peticion: esquemas.PeticionServicioCreate, username: str):
    
    adjusted_lat, adjusted_lon = adjust_location(peticion.latitud, peticion.longitud)
    
    db_peticion = databaseORM.PeticionServicio(
        username=username,
        titulo=peticion.titulo,
        descripcion=peticion.descripcion,
        precio=peticion.precio,
        fecha=peticion.fecha,
        latitud=adjusted_lat,
        longitud=adjusted_lon,
        categorias=peticion.categorias,
        location=f'POINT({peticion.longitud} {peticion.latitud})'
    )
    db.add(db_peticion)
    db.commit()
    db.refresh(db_peticion)
    return db_peticion



"""
Metodo para obtener la información de una petición/servicio

@params db: Session de la base de datos
@params id: ID de la petición

@return: Petición de servicio
"""
def get_peticion(db: Session,id: int):
    return db.query(databaseORM.PeticionServicio).filter(databaseORM.PeticionServicio.id == id).first()


"""
Metodo para obtener todas las peticiones/ervicio de un usuario

@params db: Session de la base de datos
@params username: Nombre de usuario

@return: Lista de peticiones de servicio
"""
def get_user_peticiones_servicio(db: Session, username: str):
    return db.query(databaseORM.PeticionServicio).filter(databaseORM.PeticionServicio.username == username).all()



"""
Metodo para obtener todas las peticiones/ervicio de una busqueda

@params db: Session de la base de datos
@params params: Modelo de busqueda de peticiones servicio

@return: Lista de peticiones de servicio
"""
def buscar_peticiones_servicio(db: Session, params: esquemas.BusquedaPeticionServicio):
    query = db.query(databaseORM.PeticionServicio)

    if params.texto_busqueda:
        search_pattern = f'%{params.texto_busqueda}%'
        query = query.filter(databaseORM.PeticionServicio.descripcion.ilike(search_pattern))
    
    if params.categorias:
        categorias_list = [cat.strip() for cat in params.categorias.split(',')]
        query = query.filter(databaseORM.PeticionServicio.categorias.in_(categorias_list))

    if params.precio_minimo is not None:
        query = query.filter(databaseORM.PeticionServicio.precio >= params.precio_minimo)
    if params.precio_maximo is not None:
        query = query.filter(databaseORM.PeticionServicio.precio <= params.precio_maximo)
    if params.latitud and params.longitud and params.distancia_maxima:
        user_location = func.ST_MakePoint(params.longitud, params.latitud, type_=databaseORM.PeticionServicio.location)
        query = query.filter(func.ST_Distance(databaseORM.PeticionServicio.location, user_location) <= params.distancia_maxima)

    # Aplicar ordenaciones según el parámetro 'ordenar_por'
    if params.ordenar_por == 'precio_asc':
        query = query.order_by(databaseORM.PeticionServicio.precio.asc())
    elif params.ordenar_por == 'precio_desc':
        query = query.order_by(databaseORM.PeticionServicio.precio.desc())
    elif params.ordenar_por == 'distancia' and params.latitud and params.longitud:
        user_location = func.ST_MakePoint(params.longitud, params.latitud, type_=databaseORM.PeticionServicio.location)
        query = query.order_by(func.ST_Distance(databaseORM.PeticionServicio.location, user_location).asc())

    return query.limit(200).all()

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000  # Radio de la Tierra en metros
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance = R * c
    return distance
###############################################################################

################################DEALS##########################################

###############################################################################



"""
Metodo para crear un acuerdo/deal

@params db: Session de la base de datos
@params deal: Acuerdo a crear
@params username_cliente: Nombre de usuario del cliente

@return: Acuerdo creado
"""
def create_deal(db: Session, deal: esquemas.DealCreate, username_cliente: str):
    peticion = db.query(databaseORM.PeticionServicio).filter(databaseORM.PeticionServicio.id == deal.id_peticion).first()
    if not peticion:
        raise HTTPException(status_code=404, detail="Petición no encontrada")
    db_deal = databaseORM.Deal(
        nota=-1,
        username_cliente=username_cliente,
        username_host=peticion.username,  
        id_peticion=deal.id_peticion,
        aceptado=False  
    )
    db.add(db_deal)
    db.commit()
    db.refresh(db_deal)
    return db_deal


"""
Metodo para aceptar un acuerdo/deal

@params db: Session de la base de datos
@params deal_id: ID del acuerdo
@params username_host: Nombre de usuario del host

@return: Acuerdo aceptado
"""
def accept_deal(db: Session, deal_id: int, username_host: str):
    deal = db.query(databaseORM.Deal).filter(databaseORM.Deal.id == deal_id).first()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal no encontrado")
    
    if deal.username_host != username_host:
        raise HTTPException(status_code=403, detail="No autorizado para aceptar este deal")
    deal.aceptado = True
    db.commit()
    return deal


"""
Metodo para obtener los deals de un usuario

@params db: Session de la base de datos

@return: Lista de deals
"""
def get_user_deals(db: Session, username: str):
    user_deals = db.query(databaseORM.Deal).filter(
        or_(
            databaseORM.Deal.username_cliente == username,
            databaseORM.Deal.username_host == username
        )
    ).all()
    return user_deals