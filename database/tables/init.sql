-- Create PostGIS extension if not exists
CREATE EXTENSION IF NOT EXISTS postgis;

-- Create the text search configuration for Spanish
CREATE TEXT SEARCH CONFIGURATION spanish (COPY = pg_catalog.simple);

-- Add mappings for the Spanish dictionary
ALTER TEXT SEARCH CONFIGURATION spanish
    ALTER MAPPING FOR hword, hword_part, word
    WITH spanish_stem;


-- Crear la tabla de usuarios
CREATE TABLE IF NOT EXISTS usuarios (
    username VARCHAR(50) PRIMARY KEY,
    contraseña VARCHAR(100),
    nombre_apellido VARCHAR(100) NOT NULL,
    edad INT,
    latitud DOUBLE PRECISION,
    longitud DOUBLE PRECISION,
    mail VARCHAR(100),
    telefono VARCHAR(20),
    sexo CHAR(1), -- Considera usar 'M', 'F', 'O' (Otro)
    descripcion TEXT,
    suscripciones VARCHAR(100)
);

-- Crear la tabla de peticion_servicio
CREATE TABLE IF NOT EXISTS peticion_servicio (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) REFERENCES usuarios(username),
    titulo VARCHAR(100),
    peticion BOOLEAN, -- TRUE para petición, FALSE para servicio
    descripcion TEXT,
    precio DECIMAL(10, 2),
    fecha TIMESTAMP,
    latitud DOUBLE PRECISION,
    longitud DOUBLE PRECISION,
    categorias VARCHAR(100),
    location GEOGRAPHY(POINT, 4326)
    );

-- Crear la tabla de deals/acuerdos
CREATE TABLE IF NOT EXISTS deal (
    id SERIAL PRIMARY KEY,
    nota TEXT,
    username_cliente VARCHAR(50) REFERENCES usuarios(username),
    username_host VARCHAR(50) REFERENCES usuarios(username),
    id_peticion INT REFERENCES peticion_servicio(id),
    aceptado BOOLEAN
);

-- Índices para mejorar el rendimiento en búsquedas
CREATE INDEX idx_usuario ON usuarios(username);
CREATE INDEX idx_peticion_servicio ON peticion_servicio(username);
CREATE INDEX idx_deal_cliente ON deal(username_cliente);
CREATE INDEX idx_deal_host ON deal(username_host);