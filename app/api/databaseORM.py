from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Date, Float, BigInteger,Text,DECIMAL
from sqlalchemy.orm import relationship
from .database import Base
import datetime
from datetime import date
from geoalchemy2 import Geography

class Usuario(Base):
    __tablename__ = 'usuarios'
    username = Column(String(50), primary_key=True, index=True)
    contraseña= Column(String(100))
    nombre_apellido = Column(String(100), nullable=False)
    edad = Column(Integer)
    latitud = Column(Float)
    longitud = Column(Float)
    mail = Column(String(100))
    telefono = Column(String(20))
    sexo = Column(String(1))  # 'M', 'F', 'O'
    descripcion = Column(Text)
    suscripciones = Column(String(100))

class PeticionServicio(Base):
    __tablename__ = 'peticion_servicio'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), ForeignKey('usuarios.username'))
    titulo = Column(String(100))
    peticion = Column(Boolean)  # True para petición, False para servicio
    descripcion = Column(Text)
    precio = Column(DECIMAL(10, 2))
    fecha = Column(Date)
    latitud = Column(Float)
    longitud = Column(Float)
    categorias = Column(String(100))
    usuario = relationship("Usuario")
    location = Column(Geography(geometry_type='POINT', srid=4326))

    # Generate the geography column data from latitud and longitud
    @property
    def generate_location(self):
        if self.latitud and self.longitud:
            return f'POINT({self.longitud} {self.latitud})'
        return None

class Deal(Base):
    __tablename__ = 'deal'
    id = Column(Integer, primary_key=True, index=True)
    nota = Column(Text)
    username_cliente = Column(String(50), ForeignKey('usuarios.username'))
    username_host = Column(String(50), ForeignKey('usuarios.username'))
    id_peticion = Column(Integer, ForeignKey('peticion_servicio.id'))
    aceptado = Column(Boolean)
    cliente = relationship("Usuario", foreign_keys=[username_cliente])
    host = relationship("Usuario", foreign_keys=[username_host])
    peticion_servicio = relationship("PeticionServicio")