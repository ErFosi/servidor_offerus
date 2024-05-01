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
import random

app = FastAPI()
"""
#Firebase
credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
firebase_credentials = credentials.Certificate(credentials_path)
firebase_admin.initialize_app(firebase_credentials)
mensajes_notificaciones = [
    "El tiempo debe ser repartido en todo tipo de actividades, deporte formacion e incluso ocio.",
    "Gastar demasiado tiempo en ocio es peligroso!",
    "Apuntar el tiempo de cada tarea te puede ayudar a gestionar mejor tu dia a dia",
    "El algoritmo de Shor es muy complejo!",
    "Recuerda apuntar el tiempo invertido de tus tareas!",
    "Ten un buen día y distribuye bien el tiempo!"
]
"""
lista_categorias=["gratis","deporte","entretenimiento","academico","hogar","online","otros"]
# Función para enviar mensaje aleatorio
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
    db_user = crud.get_usuario(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    crud.create_user(db=db, user=user)
    return JSONResponse(content={"message": "User created successfully"}, status_code=status.HTTP_200_OK)


@app.get("/usuario", response_model=UsuarioDetails, tags=["Usuarios"])
def read_user( db: Session = Depends(get_db),current_user: Usuario = Depends(obtener_usuario_actual)):
    db_user = crud.get_usuario(db, username=current_user.username)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


###----------------------Peticiones de Servicio------------------------###


#Esta ruta sirve para obtener un usuario en especifico
@app.post("/peticiones_servicio", response_model=PeticionServicioCreate, tags=["Peticion Servicio"])
def add_peticion_servicio(peticion: PeticionServicioCreate, db: Session = Depends(get_db), current_user: Usuario = Depends(obtener_usuario_actual)):
    try:
        return crud.create_peticion_servicio(db=db, peticion=peticion, username=current_user.username)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    
#Esta ruta sirve para crear un nuevo deal
@app.post("/deals", response_model=DealCreate, tags=["Peticion Servicio"])
def create_deal(deal: DealCreate, db: Session = Depends(get_db), current_user: Usuario = Depends(obtener_usuario_actual)):
    return crud.create_deal(db=db, deal=deal,username_cliente=current_user.username)

#Esta ruta sirve para aceptar un deal
@app.post("/deals/accept", response_model=DealCreate, tags=["Peticion Servicio"])
def accept_deal(deal_id: int, db: Session = Depends(get_db), current_user: Usuario = Depends(obtener_usuario_actual)):
    return crud.accept_deal(db=db, deal_id=deal_id, username_host=current_user.username)

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

########### busqueda ###########
@app.post("/buscar_peticiones_servicio",response_model=List[PeticionServicioResponse],tags=["Busqueda"])
def buscar_peticiones_servicio(busqueda: BusquedaPeticionServicio, db: Session = Depends(get_db)):
    result = crud.buscar_peticiones_servicio(db, busqueda)
    return result

@app.get("/usuarios/mis_deals", response_model=List[DealResponse], tags=["Deals"])
def read_user_deals(db: Session = Depends(get_db), current_user: Usuario = Depends(obtener_usuario_actual)):
    deals = crud.get_user_deals(db, username=current_user.username)
    return deals

###----------------------Oauth------------------------###

#Esta ruta sirve para obtener el token de acceso
@app.post("/token",tags=["Oauth"], response_model=TokenConUsuario)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    usuario = crud.authenticate_user(db, form_data.username, form_data.password)
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Generar el token de acceso
    access_token_expires = timedelta(minutes=30)  # O el tiempo que consideres adecuado
    access_token = crear_token_acceso(
        data={"sub":str(usuario.username)}
    )

    # Generar el refresh token
    refresh_token_expires = timedelta(days=7)  # Los refresh tokens suelen tener una mayor duración
    refresh_token = crear_token_acceso(  # Suponiendo que reutilizas la misma función con un parámetro adicional
        data={"sub": str(usuario.username),"refresh":True}
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
@app.post("/sub_a_act", tags=["Firebase"])
async def subscribe_to_actividades(token: FirebaseClientToken,usuario_actual: Usuario = Depends(obtener_usuario_actual)):
    try:
        
        token_string = token.fcm_client_token
        print(token_string)
        response = messaging.subscribe_to_topic([token_string], 'actividades')
        
        
        return {"message": "Subscribed to actividades", "response": response}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    
@app.post("/testactividades", tags=["Firebase"])
async def test_actividades(usuario_actual: Usuario = Depends(obtener_usuario_actual)):
    # Elegir un mensaje aleatorio de la lista
    mensaje_aleatorio = random.choice(mensajes_notificaciones)
    
    # Crear el mensaje de FCM
    message = messaging.Message(
        notification=messaging.Notification(
            title="Recordatorio Importante",
            body=mensaje_aleatorio,
        ),
        topic="actividades"
    )
    
    # Enviar el mensaje a través de FCM
    try:
        response = messaging.send(message)
        return {"message": "Message sent to topic /actividades", "response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

