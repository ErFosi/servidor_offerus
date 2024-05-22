from typing import Union
import os
import logging
from fastapi import FastAPI
from google.auth import jwt
from sqlalchemy.orm import Session
from .database import SessionLocal
from fastapi import Depends, HTTPException, status,UploadFile
from fastapi.security import OAuth2PasswordRequestForm
from typing import List
from .databaseORM import Usuario,PeticionServicio,Deal
from .esquemas import *
from . import crud
from fastapi.responses import FileResponse
from fastapi.responses import JSONResponse
from .oauth import obtener_usuario_actual, crear_token_acceso, SECRET_KEY
from datetime import datetime, timedelta
import glob
import firebase_admin
from firebase_admin import credentials, messaging
import google.auth
from google.auth.transport.requests import Request
from os import environ
from google.oauth2 import service_account
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import requests
import random
import io
from unidecode import unidecode
from geopy.geocoders import Nominatim
from nltk.corpus import stopwords

app = FastAPI()
geolocator = Nominatim(user_agent="offerus")



#Firebase
credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
firebase_credentials = credentials.Certificate(credentials_path)
firebase_admin.initialize_app(firebase_credentials)

def enviar_mensaje_fcm(tema: str, titulo: str, cuerpo: str):
    print("Se envia mensaje a tema: ",tema)
    # Crear un mensaje de notificación
    message = messaging.Message(
        notification=messaging.Notification(
            title=titulo,
            body=cuerpo,
        ),
        topic=tema
    )
    
    # Enviar el mensaje
    try:
        response = messaging.send(message)
        return {"message": "Mensaje enviado con éxito", "response": response}
    except Exception as e:
        return {"error": str(e)}

lista_categorias=["gratis","deporte","entretenimiento","academico","hogar","online","otros"]
# Función para enviar mensaje aleatorio
""" 
def enviar_mensaje_aleatorio():
    mensaje_aleatorio = random.choice(mensajes_notificaciones)
    message = messaging.Message(
        notification=messaging.Notification(
            title="Recordatorio Importante",
            body=mensaje_aleatorio,
        ),
        topic="actividades"
    )
    try:
        response = messaging.send(message)
        print(f"Mensaje enviado: {response}")
    except Exception as e:
        print(f"Error enviando mensaje: {str(e)}")
"""
"""
scheduler = AsyncIOScheduler()
scheduler.add_job(
    enviar_mensaje_aleatorio,
    CronTrigger(hour='*/1'),  # Ejecutar todos los días a las 10:00 AM
    timezone="UTC"  # Zona horaria de España
)
print("------------------AUTO NOTIFICATIONS ON-------------------")
scheduler.start()
"""



VALID_IMG_TYPES = ['image/jpeg', 'image/png', 'image/webp']

image_folder = "/code/images"



def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
###----------------------Rutas------------------------###



###----------------------Usuarios------------------------###
#Esta ruta sirve para
@app.post("/usuarios", status_code=status.HTTP_200_OK, tags=["Usuarios"])
def crear_usuarios(user: UsuarioCreate, db: Session = Depends(get_db)):
    # Eliminar espacios en blanco al principio y al final del nombre de usuario
    username = user.username.rstrip()
    
    db_user = crud.get_usuario(db, username=username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Crear el usuario con el nombre de usuario limpio
    user.username = username
    crud.create_user(db=db, user=user)
    
    return JSONResponse(content={"message": "User created successfully"}, status_code=status.HTTP_200_OK)


@app.get("/usuario", response_model=UsuarioDetails, tags=["Usuarios"])
def read_user( db: Session = Depends(get_db),current_user: Usuario = Depends(obtener_usuario_actual)):
    db_user = crud.get_usuario(db, username=current_user.username)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@app.get("/usuario_details", response_model=UsuarioDetails, tags=["Usuarios"])
def read_user(username:str, db: Session = Depends(get_db)):
    db_user = crud.get_usuario(db, username=username)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

#ruta para modificar el usuario
@app.put("/usuario", response_model=UsuarioDetails, tags=["Usuarios"])
def update_user(user_update: UsuarioUpdate, db: Session = Depends(get_db), current_user: Usuario = Depends(obtener_usuario_actual)):
    # Asegúrate de que estás pasando 'current_user.username' correctamente como una cadena
    db_user = crud.update_user(db, current_user.username, user_update)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@app.put("/usuario/cambiar_contraseña", response_model=UsuarioDetails, tags=["Usuarios"])
def cambiar_contraseña(cambio: UsuarioModContraseña, db: Session = Depends(get_db), current_user: Usuario = Depends(obtener_usuario_actual)):
    # Usar el nombre de usuario del usuario actual para la modificación
    db_user = crud.modificar_contraseña(db, current_user.username, cambio)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

###----------------------Peticiones de Servicio------------------------###


#Esta ruta sirve para crear una peticion servicio
@app.post("/peticiones_servicio", response_model=PeticionServicioCreate, tags=["Peticion Servicio"])
def add_peticion_servicio(peticion: PeticionServicioCreate, db: Session = Depends(get_db), current_user: Usuario = Depends(obtener_usuario_actual)):
    try:
        pet_Creada= crud.create_peticion_servicio(db=db, peticion=peticion, username=current_user.username)
        categorias = [categoria.strip() for categoria in peticion.categorias.split(',')]
        provincia=getProvincia(current_user.latitud,current_user.longitud)
        print(provincia)
        for categoria in categorias:
            titulo = "Nueva petición de servicio en tu categoría"
            cuerpo = f"{peticion.titulo} - {peticion.descripcion[:50]}..."  # Resumen de la descripción
            
            if categoria!="online":
                enviar_mensaje_fcm(f"{categoria}_{provincia}", titulo, cuerpo)
            else:
                enviar_mensaje_fcm(categoria, titulo, cuerpo)
        return pet_Creada
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    


#Esta ruta sirve para obtener todas las peticiones del usuario autenticado
@app.get("/usuarios/peticiones_servicio", response_model=List[PeticionServicioResponse], tags=["Peticion Servicio"])
def read_user_peticiones_servicio( db: Session = Depends(get_db), current_user: Usuario = Depends(obtener_usuario_actual)):
    peticiones = crud.get_user_peticiones_servicio(db, username=current_user.username)
    return peticiones

#Esta ruta sirve para obtener una peticion en especifico
@app.get("/peticion", response_model=PeticionServicioDetails, tags=["Peticion Servicio"])
def get_peticion( id_pet: int, db: Session = Depends(get_db)):
    db_pet = crud.get_peticion(db, id=id_pet)
    if db_pet is None:
        raise HTTPException(status_code=404, detail="Peticion not found")
    return db_pet
#Esta ruta sirve para obtener una lista de peticiones en especifico
@app.post("/peticiones", response_model=List[PeticionServicioDetails], tags=["Peticion Servicio"])
def get_peticiones(request: PeticionesRequest, db: Session = Depends(get_db)):
    db_peticiones = crud.get_peticiones(db, ids=request.ids_pet)
    if not db_peticiones:
        raise HTTPException(status_code=404, detail="Peticiones not found")
    return db_peticiones

@app.put("/peticiones_servicio", response_model=PeticionServicioDetails, tags=["Peticion Servicio"])
def update_peticion_servicio (peticion: PeticionServicioUpdate, db: Session = Depends(get_db), current_user: Usuario = Depends(obtener_usuario_actual)):
    existing_pet = crud.get_peticion(db, id=peticion.id)
    if not existing_pet:
        raise HTTPException(status_code=404, detail="Peticion not found")
    if existing_pet.username != current_user.username:
        raise HTTPException(status_code=403, detail="Not authorized to update this peticion")

    updated_peticion = crud.update_peticion_servicio(db=db, peticion_update=peticion, username=current_user.username)
    return updated_peticion

#ruta para eliminar una peticion
@app.delete("/peticiones_servicio", response_model=PeticionServicioDetails, tags=["Peticion Servicio"])
def delete_peticion_servicio(id_pet: int, db: Session = Depends(get_db), current_user: Usuario = Depends(obtener_usuario_actual)):
    existing_pet = crud.get_peticion(db, id=id_pet)
    if not existing_pet:
        raise HTTPException(status_code=404, detail="Peticion not found")
    if existing_pet.username != current_user.username:
        raise HTTPException(status_code=403, detail="Not authorized to delete this peticion")

    deleted_pet = crud.delete_peticion_servicio(db, id=id_pet, username=current_user.username)
    return deleted_pet
###----------------------Deals------------------------###
#Esta ruta sirve para crear un nuevo deal
@app.post("/deals", response_model=DealCreate, tags=["Deals"])
def create_deal(deal: DealCreate, db: Session = Depends(get_db), current_user: Usuario = Depends(obtener_usuario_actual)):
    created_deal = crud.create_deal(db=db, deal=deal, username_cliente=current_user.username)
    
    # Obtener el usuario creador de la petición
    peticion = crud.get_peticion(db, id=created_deal.id_peticion)
    creador_peticion = crud.get_usuario(db, peticion.username)
    
    # Enviar notificación si el creador desea recibir notificaciones
    
    titulo = "Nuevo deal en tu petición"
    cuerpo = f"{current_user.username} ha realizado un deal en tu petición: {peticion.titulo}"
    enviar_mensaje_fcm(unidecode(f"user_{creador_peticion.username}"), titulo, cuerpo)
    
    return created_deal

#Esta ruta sirve para aceptar un deal
@app.post("/deals/accept_deny", response_model=DealCreate, tags=["Deals"])
def accept_deny_deal(action: DealAction, db: Session = Depends(get_db), current_user: Usuario = Depends(obtener_usuario_actual)):
    updated_deal = crud.accept_deny_deal(db=db, deal_id=action.deal_id, username_host=current_user.username, accept=action.accept)
    
    # Enviar notificación al cliente del deal
    deal_info = crud.get_deal(db, id=action.deal_id)
    cliente_deal = crud.get_usuario(db, deal_info.username_cliente)
    peticion= crud.get_peticion(db, id=deal_info.id_peticion)
    accion = "aceptado" if action.accept else "rechazado"
    titulo = "Tu deal ha sido " + accion
    cuerpo = f"Tu deal en la petición '{peticion.titulo}' ha sido {accion}."
    
    enviar_mensaje_fcm(unidecode(f"user_{deal_info.username_cliente}"), titulo, cuerpo)
    
    return updated_deal

@app.post("/deals/valorar", response_model=DealResponse, tags=["Deals"])
def valorar_deal(rate: RateDeal, db: Session = Depends(get_db), current_user: Usuario = Depends(obtener_usuario_actual)):
    return crud.rate_deal(db=db, deal_id=rate.deal_id, username=current_user.username, nota=rate.nota)


########### busqueda ###########
@app.post("/buscar_peticiones_servicio",response_model=List[PeticionServicioResponse],tags=["Busqueda"])
def buscar_peticiones_servicio(busqueda: BusquedaPeticionServicio, db: Session = Depends(get_db)):
    result = crud.buscar_peticiones_servicio(db, busqueda)
    return result

@app.get("/usuarios/mis_deals", response_model=List[DealResponse], tags=["Deals"])
def read_user_deals(db: Session = Depends(get_db), current_user: Usuario = Depends(obtener_usuario_actual)):
    deals = crud.get_user_deals(db, username=current_user.username)
    return deals

@app.get("/usuario/nota", response_model=NotaResponse, tags=["Usuarios"])
def get_nota_usuario(username:str, db: Session = Depends(get_db)):
    nota, cant = crud.get_nota_usuario(db, username)
    return NotaResponse(nota=nota, cant=cant)
###----------------------Oauth------------------------###

#Esta ruta sirve para obtener el token de acceso
@app.post("/token", tags=["Oauth"], response_model=TokenConUsuario)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # Eliminar espacios en blanco al final del nombre de usuario
    username = form_data.username.rstrip()
    
    usuario = crud.authenticate_user(db, username, form_data.password)
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Generar el token de acceso
    access_token_expires = timedelta(minutes=300000)  # O el tiempo que consideres adecuado
    access_token = crear_token_acceso(
        data={"sub": str(usuario.username)}
    )

    # Generar el refresh token
    refresh_token_expires = timedelta(days=90)  # Los refresh tokens suelen tener una mayor duración
    refresh_token = crear_token_acceso(  # Suponiendo que reutilizas la misma función con un parámetro adicional
        data={"sub": str(usuario.username), "refresh": True}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": refresh_token
    }


###----------------------Profile_picture------------------------###

#Esta ruta sirve para obtener la imagen de perfil de un usuario cualquiera
@app.get("/profile/image", tags=["Foto"], status_code=status.HTTP_200_OK, response_class=FileResponse)
async def get_user_profile_image(usuario_actual: str, db: Session = Depends(get_db)):
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    VALID_IMG_EXT = ['.jpeg', '.png', '.webp', '.jpg']
    enc=False
    # Intenta encontrar una imagen que coincida con las extensiones válidas
    for extension in VALID_IMG_EXT:
        image_path = os.path.join(image_folder, f"{usuario_actual}{extension}")
        if os.path.isfile(image_path):
            enc=True
            return FileResponse(image_path)
        
    if (not enc):
        # Si no se encuentra ninguna imagen válida, devuelve la imagen predeterminada
        default_image_path = os.path.join(image_folder, "default.jpg")
        if not os.path.isfile(default_image_path):
            raise HTTPException(status_code=404, detail="Default image not found.")
        return FileResponse(default_image_path)

#Esta ruta sirve para subir una imagen de perfil asociado a un usuario autenticado
@app.post("/profile/image", tags=["Foto"], status_code=status.HTTP_201_CREATED)
async def upload_user_profile_image(file: UploadFile, usuario_actual: Usuario = Depends(obtener_usuario_actual), db: Session = Depends(get_db)):
    
    if file.content_type not in ['image/jpeg', 'image/png', 'image/webp']:
        raise HTTPException(status_code=400, detail="Invalid file type")

  
    pattern = f"{usuario_actual.username}.*"
    search_path = os.path.join(image_folder, pattern)

    
    existing_files = glob.glob(search_path)
    for file_path in existing_files:
        try:
            os.remove(file_path)
        except Exception as e:
            
            raise HTTPException(status_code=500, detail="Could not remove existing file")

    
    extension = os.path.splitext(file.filename)[1]  
    file_name = f"{usuario_actual.username}{extension}"
    file_path = os.path.join(image_folder, file_name)

    contents = await file.read()
    with open(file_path, 'wb') as f:
        f.write(contents)

    return {"filename": file_name}

###----------------------Firebase------------------------### (aun no terminado)

topics=["deportes","academico","hogar","gratis","online","entretenimiento","otros"]
@app.post("/suscribir_fcm", tags=["FCM"])
async def suscribir_fcm(token: FirebaseClientToken, db: Session = Depends(get_db), current_user: Usuario = Depends(obtener_usuario_actual)):
    # Obtener el usuario
    usuario = crud.get_usuario(db, current_user.username)
    provincia=getProvincia(usuario.latitud,usuario.longitud)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Desuscribir el token FCM de todos los temas
    
    for topic in topics:
        try:
            response = messaging.unsubscribe_from_topic([token.fcm_client_token], f"{topic.strip()}_{provincia}")
            print(f"Desuscripción de {topic.strip()}_{provincia}: {response}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al desuscribir de {topic}: {str(e)}")
    
    # Suscribir el token FCM al tema del usuario
    user_topic = unidecode(f"user_{current_user.username}")
    try:
        response_user_topic = messaging.subscribe_to_topic([token.fcm_client_token], user_topic)
        print(f"Suscrito al tema del usuario {user_topic}: {response_user_topic}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al suscribir al tema del usuario: {str(e)}")
    
    # También suscribir a categorías, si es necesario
    categorias = usuario.suscripciones
    provincia=getProvincia(usuario.latitud,usuario.longitud)
    
 
# Display
    print(provincia)
    print(categorias)
    if categorias != "":
        categorias_sep= categorias.split(",")
   
        for categoria in categorias_sep:
            if categoria != "":
                print(categoria.strip())
                try:
                    
                    if categoria!="online":
                        print(f"{categoria.strip()}_{provincia}")
                        response_categoria2 = messaging.subscribe_to_topic([token.fcm_client_token], f"{categoria.strip()}_{provincia}")
                        print(f"Suscrito a f'{categoria.strip()}_{provincia}': {response_categoria2}")
                    else:
                        response_categoria = messaging.subscribe_to_topic([token.fcm_client_token], categoria.strip())
                        print(f"Suscrito a {categoria}: {response_categoria}")

                except Exception as e:
                    raise HTTPException(status_code=500, detail=f"Error al suscribir a la categoría {categoria}: {str(e)}")

        return {"message": "Suscripción a FCM realizada con éxito para el usuario y sus categorías indicadas"}
    else:
        print("No se han indicado categorías")
    



### Dar favorito a una peticion de servicio ###

@app.post("/favoritos", tags=["Favs"])
async def fav_peticion_servicio(favoritos: FavCreate, db: Session = Depends(get_db), current_user: Usuario = Depends(obtener_usuario_actual)):
    return crud.fav_peticion_servicio(db, id_peticion=favoritos.id_peticion, username=current_user.username)

### Obtener favoritos de un usuario ###

@app.get("/favoritos", tags=["Favs"])
async def get_favoritos(db: Session = Depends(get_db), current_user: Usuario = Depends(obtener_usuario_actual)):
    return crud.get_favoritos(db, current_user.username)

### Eliminar fav a una peticion de servicio ###
@app.delete("/favoritos", tags=["Favs"])
async def unfav_peticion_servicio(favoritos: FavCreate, db: Session = Depends(get_db), current_user: Usuario = Depends(obtener_usuario_actual)):
    return crud.unfav_peticion_servicio(db, id_peticion=favoritos.id_peticion, username=current_user.username)



def getProvincia(lat,long):
    print("Obteniendo provincia a partir de coordenadas",lat,long)
    location = geolocator.reverse(str(lat) + "," + str(long))
    try:
        adress = location.raw["address"]
        provincia=adress.get("state","")
        provincia = unidecode(provincia.replace(" ", "").lower())
        return provincia
    except:
        return ""