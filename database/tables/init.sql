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
    descripcion VARCHAR(400),
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

-- Crear la tabla de deals/acuerdos con notas para cliente y host
CREATE TABLE IF NOT EXISTS deal (
    id SERIAL PRIMARY KEY,
    username_cliente VARCHAR(50) REFERENCES usuarios(username),
    username_host VARCHAR(50) REFERENCES usuarios(username),
    id_peticion INT REFERENCES peticion_servicio(id) ON DELETE CASCADE,
    estado VARCHAR(10) DEFAULT 'pendiente', -- Puede ser 'aceptado', 'rechazado', o 'pendiente'
    nota_cliente INT DEFAULT -1, -- Nota asignada al cliente, -1 como valor por defecto indicando no evaluado
    nota_host INT DEFAULT -1 -- Nota asignada al host, -1 como valor por defecto indicando no evaluado
);

-- Crear la tabla de likes
CREATE TABLE IF NOT EXISTS favoritos (
    username VARCHAR(50),
    id_peticion INT,
    PRIMARY KEY (username, id_peticion),
    FOREIGN KEY (username) REFERENCES usuarios(username) ON DELETE CASCADE,
    FOREIGN KEY (id_peticion) REFERENCES peticion_servicio(id) ON DELETE CASCADE
);

-- Índices para mejorar el rendimiento en búsquedas
CREATE INDEX idx_usuario ON usuarios(username);
CREATE INDEX idx_peticion_servicio ON peticion_servicio(username);
CREATE INDEX idx_deal_cliente ON deal(username_cliente);
CREATE INDEX idx_deal_host ON deal(username_host);

-- Índice para mejorar la búsqueda de likes por usuario
CREATE INDEX idx_likes_username ON likes(username);

-- Índice para mejorar la búsqueda de likes por petición
CREATE INDEX idx_likes_peticion ON likes(id_peticion);

-- Índice para ordenar o filtrar likes por fecha
CREATE INDEX idx_likes_fecha ON likes(fecha_like);

-- Insertar un usuario default en la tabla de usuarios
INSERT INTO usuarios (
    username,
    contraseña,
    nombre_apellido,
    edad,
    latitud,
    longitud,
    mail,
    telefono,
    sexo,
    descripcion,
    suscripciones
) VALUES (
    'default_user',
    'pbkdf2-sha256$29000$AH6lAX6lAH6=$1mgDx5elxdXGdyiShvLjR5xha.ShUDGjDPPdcWR6Trg=', 
    'Usuario Predeterminado',
    NULL, -- Edad no especificada
    NULL, -- Latitud no especificada
    NULL, -- Longitud no especificada
    'default@mail.com',
    '0000000000',
    'O', -- Sexo 'Otro' queria helicoptero apache de combate pero aimar no me deja
    'Este es un usuario por defecto.',
    NULL
);