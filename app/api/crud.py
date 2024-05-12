from passlib.context import CryptContext
from typing import List
from . import databaseORM
from . import esquemas
from sqlalchemy.orm import Session
from fastapi import HTTPException
import random
from sqlalchemy import func
import math
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from geoalchemy2 import Geography
from geoalchemy2.functions import ST_DistanceSphere, ST_MakePoint
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

def update_user(db: Session, username: str, user_update: esquemas.UsuarioUpdate):
    db_user = db.query(databaseORM.Usuario).filter(databaseORM.Usuario.username == username).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    for attr, value in user_update.dict(exclude_unset=True).items():
        setattr(db_user, attr, value)
    
    db.commit()
    db.refresh(db_user)
    return db_user

def modificar_contraseña(db: Session, username: str, user: esquemas.UsuarioModContraseña):
    db_user = db.query(databaseORM.Usuario).filter(databaseORM.Usuario.username == username).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Verificar que la contraseña actual es correcta
    if not verify_password(user.contraseña, db_user.contraseña):
        raise HTTPException(status_code=417, detail="Contraseña incorrecta")
    
    # Hash de la nueva contraseña y actualización
    db_user.contraseña = hash_password(user.nueva_contraseña)
    db.commit()
    db.refresh(db_user)
    return db_user

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
        peticion=peticion.peticion,
        precio=peticion.precio,
        fecha=peticion.fecha,
        latitud=adjusted_lat,
        longitud=adjusted_lon,
        categorias=peticion.categorias,
        location=f'POINT({adjusted_lon} {adjusted_lat})'
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
Metodo para obtener varias peticiones/servicio

@params db: Session de la base de datos
@params ids: Lista de IDs de las peticiones

@return: Lista de peticiones de servicio
"""
def get_peticiones(db: Session, ids: List[int]):
    return db.query(databaseORM.PeticionServicio).filter(databaseORM.PeticionServicio.id.in_(ids)).all()


"""
Metodo para obtener todas las peticiones/ervicio de un usuario

@params db: Session de la base de datos
@params username: Nombre de usuario

@return: Lista de peticiones de servicio
"""
def get_user_peticiones_servicio(db: Session, username: str):
    return db.query(databaseORM.PeticionServicio).filter(databaseORM.PeticionServicio.username == username).all()

"""
Metodo para modificar una petición/servicio

@params db: Session de la base de datos
@params peticion_update: Modelo de actualización de la petición
@params username: Nombre de usuario

@return: Petición de servicio actualizada
"""
def update_peticion_servicio(db: Session, peticion_update: esquemas.PeticionServicioUpdate, username: str):
    # Buscar la petición existente en la base de datos
    db_peticion = db.query(databaseORM.PeticionServicio).filter(databaseORM.PeticionServicio.id == peticion_update.id).first()
    
    if not db_peticion:
        raise HTTPException(status_code=404, detail="Petición no encontrada")
    
    if db_peticion.username != username:
        raise HTTPException(status_code=403, detail="Unauthorized")

    # Preparar para actualizar la latitud y longitud
    should_update_location = peticion_update.latitud is not None and peticion_update.longitud is not None
    if should_update_location:
        adjusted_lat, adjusted_lon = adjust_location(peticion_update.latitud, peticion_update.longitud)

    # Actualizar los campos en la instancia de la base de datos
    for key, value in peticion_update.dict(exclude_unset=True, exclude={'latitud', 'longitud'}).items():
        if hasattr(db_peticion, key):
            setattr(db_peticion, key, value)

    # Ajustar la latitud y longitud si están presentes en la actualización
    if should_update_location:
        db_peticion.latitud = adjusted_lat
        db_peticion.longitud = adjusted_lon
        db_peticion.location = f'POINT({adjusted_lon} {adjusted_lat})'

    # Guardar los cambios en la base de datos
    db.commit()
    db.refresh(db_peticion)
    
    return db_peticion

""" 
Metodo para eliminar una petición/servicio

@params db: Session de la base de datos
@params id: ID de la petición
@params username: Nombre de usuario

@return: Petición de servicio eliminada
"""
def delete_peticion_servicio(db: Session, id: int, username: str):
    db_peticion = db.query(databaseORM.PeticionServicio).filter(databaseORM.PeticionServicio.id == id).first()
    if not db_peticion:
        raise HTTPException(status_code=404, detail="Petición no encontrada")
    
    if db_peticion.username != username:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    db.delete(db_peticion)
    db.commit()
    return db_peticion


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
    print(params.latitud, params.longitud, params.distancia_maxima )
    if params.latitud is not None and params.longitud is not None and params.distancia_maxima is not None:
            
        user_location = func.ST_MakePoint(params.longitud, params.latitud)
        print(f"User Location: {user_location}, Distance Max: {params.distancia_maxima}")
        # Ensure the distance function matches the data type
        # Using ST_Distance for geography type, which returns meters
        query = query.filter(
            func.ST_Distance(
                databaseORM.PeticionServicio.location, 
                user_location
            ) <= params.distancia_maxima*1000
        )

    print(query) 

    # Aplicar ordenaciones según el parámetro 'ordenar_por'
    if params.ordenar_por == 'precio_asc':
        query = query.order_by(databaseORM.PeticionServicio.precio.asc())
    elif params.ordenar_por == 'precio_desc':
        query = query.order_by(databaseORM.PeticionServicio.precio.desc())
    elif params.ordenar_por == 'distancia' and params.latitud and params.longitud:
        user_location = ST_MakePoint(params.longitud, params.latitud)
        query = query.order_by(
            ST_DistanceSphere(
                databaseORM.PeticionServicio.location, 
                user_location
            ).asc()
        )

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
Metodo para crear un acuerdo/deal, el username cliente no puede coincidir con el username del host

@params db: Session de la base de datos
@params deal: Acuerdo a crear
@params username_cliente: Nombre de usuario del cliente

@return: Acuerdo creado
"""
def create_deal(db: Session, deal: esquemas.DealCreate, username_cliente: str):
    # Buscar la petición asociada al deal que se desea crear
    peticion = db.query(databaseORM.PeticionServicio).filter(databaseORM.PeticionServicio.id == deal.id_peticion).first()
    
    # Verificar que la petición existe
    if not peticion:
        raise HTTPException(status_code=404, detail="Petición no encontrada")
    
    # Verificar que el cliente no sea el mismo que el host
    if peticion.username == username_cliente:
        raise HTTPException(status_code=400, detail="El cliente no puede ser el mismo que el host")
    
    # Crear el acuerdo/deal
    db_deal = databaseORM.Deal(
        username_cliente=username_cliente,
        username_host=peticion.username,
        id_peticion=deal.id_peticion,
        estado='pendiente',  # Assume default estado is 'pendiente'
        nota_cliente=-1,  # Correctly initializing nota_cliente
        nota_host=-1,  # Correctly initializing nota_host
    )
    
    # Agregar el deal a la base de datos y confirmar cambios
    db.add(db_deal)
    db.commit()
    db.refresh(db_deal)
    
    # Retornar el acuerdo creado
    return db_deal

"""
Metodo para aceptar un acuerdo/deal

@params db: Session de la base de datos
@params deal_id: ID del acuerdo
@params username_host: Nombre de usuario del host
@params accept: Booleano para saber si rechazar o aceptar la deny

@return: Acuerdo aceptado
"""
def accept_deny_deal(db: Session, deal_id: int, username_host: str, accept: bool):
    deal = db.query(databaseORM.Deal).filter(databaseORM.Deal.id == deal_id).first()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal no encontrado")
    
    if deal.username_host != username_host:
        raise HTTPException(status_code=403, detail="No autorizado para aceptar o rechazar este deal")
    
    if deal.estado != 'pendiente':
        raise HTTPException(status_code=409, detail="Solo se pueden modificar deals que están en estado pendiente")

    deal.estado = 'aceptado' if accept else 'rechazado'
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

"""
Metodo para valorar una deal

@params db: Session de la base de datos
@params deal_id: Id del deal
@params username: Usuario que valora
@params Nota: Nota a valorar

@return: Lista de deals
"""
def rate_deal(db: Session, deal_id: int, username: str, nota: int):
    deal = db.query(databaseORM.Deal).filter(databaseORM.Deal.id == deal_id).first()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal no encontrado")

    # Verifica que el usuario sea el cliente o el host en el deal
    if deal.username_cliente != username and deal.username_host != username:
        raise HTTPException(status_code=403, detail="No autorizado para valorar este deal")

    # Verifica que el estado del deal permita valoración
    if deal.estado != 'aceptado':
        raise HTTPException(status_code=400, detail="Solo se pueden valorar deals aceptados")

    # Actualiza la nota correspondiente según el rol del usuario
    if deal.username_cliente == username:
        deal.nota_cliente = nota
    elif deal.username_host == username:
        deal.nota_host = nota

    db.commit()
    return deal

"""
Metodo para obtener un deal a partir del id

@params db: Session de la base de datos
@params id: id del dea


"""
def get_deal(db: Session, id: int):
    return db.query(databaseORM.Deal).filter(databaseORM.Deal.id == id).first()
"""
Metodo para dar fav a una petición

@params db: Session de la base de datos
@params username: Nombre de usuario
@params id_peticion: ID de la petición

@return: Favorito creado
"""
def fav_peticion_servicio(db: Session, username: str, id_peticion: int):
    # Check if the petition exists
    exists = db.query(databaseORM.PeticionServicio.id).filter_by(id=id_peticion).scalar() is not None
    if not exists:
        raise HTTPException(status_code=404, detail=f"Petición with id {id_peticion} not found")

    favorito = databaseORM.Favoritos(username=username, id_peticion=id_peticion)
    db.add(favorito)
    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e.orig))
    return favorito


""" 
Metodo para obtener los favs de un usuario

@params db: Session de la base de datos
@params username: Nombre de usuario

@return: Lista de peticiones favoritas del usuario
"""
def get_favoritos(db: Session, username: str):
    favoritos_peticiones = db.query(databaseORM.PeticionServicio).\
        join(databaseORM.Favoritos, databaseORM.Favoritos.id_peticion == databaseORM.PeticionServicio.id).\
        filter(databaseORM.Favoritos.username == username).all()

    return [esquemas.PeticionServicioDetails.from_orm(peticion) for peticion in favoritos_peticiones]
"""
Metodo para eliminar un fav de un usuario a una peticion

@params db: Session de la base de datos
@params username: Nombre de usuario

@return: Favorito eliminado
"""
def unfav_peticion_servicio(db: Session, username: str, id_peticion: int):
    favorito = db.query(databaseORM.Favoritos).filter(
        databaseORM.Favoritos.username == username,
        databaseORM.Favoritos.id_peticion == id_peticion
    ).first()
    if not favorito:
        raise HTTPException(status_code=404, detail="Favorito no encontrado")
    db.delete(favorito)
    db.commit()
    return favorito