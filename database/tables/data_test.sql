-- Drop and recreate the `random_point_around_bilbao` function to ensure correct functionality

-- Delete all debug requests and services
DELETE FROM peticion_servicio
WHERE username LIKE 'debug_user_%';

-- Delete all debug users
DELETE FROM usuarios
WHERE username LIKE 'debug_user_%';

DROP FUNCTION IF EXISTS random_point_around_bilbao();
CREATE OR REPLACE FUNCTION random_point_around_bilbao() RETURNS TABLE (lat DOUBLE PRECISION, lon DOUBLE PRECISION) AS $$
DECLARE
    base_lat DOUBLE PRECISION := 43.26271;  -- Latitude of Bilbao
    base_lon DOUBLE PRECISION := -2.92528;  -- Longitude of Bilbao
    radius_km INTEGER := 30;  -- Radius in km
BEGIN
    RETURN QUERY
    SELECT base_lat + (random() * 2 - 1) * radius_km / 111,
           base_lon + (random() * 2 - 1) * radius_km / (111 * COS(base_lat * PI() / 180));
END;
$$ LANGUAGE plpgsql;

-- Temporary tables for common names and surnames
CREATE TEMP TABLE nombres_comunes (nombre VARCHAR(50));
INSERT INTO nombres_comunes VALUES
    ('Antonio'), ('Jose'), ('Manuel'), ('Francisco'), ('David'), ('Juan'), ('Luis'), ('Javier'),
    ('María'), ('Carmen'), ('Ana'), ('Isabel'), ('Laura'), ('Sonia'), ('Lucía'), ('Cristina');

CREATE TEMP TABLE apellidos_comunes (apellido VARCHAR(50));
INSERT INTO apellidos_comunes VALUES
    ('García'), ('Martínez'), ('López'), ('Sánchez'), ('Pérez'), ('González'), ('Fernández'), ('Rodríguez');

-- Insert 50 users with Spanish common names
DO $$
DECLARE
    hashed_password TEXT := 'pbkdf2-sha256$29000$t5byXqu1lpKy9v7/n5NyDg$ti0on0omRoSF.pQYdNYsejDgwGaEhsx.sDbjAeD.aNs';
    i INTEGER;
    selected_nombre VARCHAR(50);
    selected_apellido1 VARCHAR(50);
    selected_apellido2 VARCHAR(50);
    user_lat DOUBLE PRECISION;
    user_lon DOUBLE PRECISION;
BEGIN
    FOR i IN 1..200 LOOP
        SELECT nombre INTO selected_nombre FROM nombres_comunes ORDER BY random() LIMIT 1;
        SELECT apellido INTO selected_apellido1 FROM apellidos_comunes ORDER BY random() LIMIT 1;
        SELECT apellido INTO selected_apellido2 FROM apellidos_comunes ORDER BY random() LIMIT 1;

        IF i % 10 = 0 THEN
            -- Use a fixed location for every 10th user
            user_lat := 37.4219999;
            user_lon := -122.084;
        ELSE
            -- Get random coordinates around Bilbao
            SELECT lat, lon INTO user_lat, user_lon FROM random_point_around_bilbao();
        END IF;

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
            format('debug_user_%s', i),
            hashed_password,
            format('%s %s %s', selected_nombre, selected_apellido1, selected_apellido2),
            25 + (i % 15),
            user_lat,
            user_lon,
            format('debug_user_%s@mail.com', i),
            format('123456789%s', i),
            'O',
            format('Este es el usuario de prueba %s con fines de depuración.', i),
            NULL
        );
    END LOOP;
END $$;

-- Create 2 requests and 1 service per user
DO $$
DECLARE
    i INTEGER;
    current_username VARCHAR(50);
    user_lat DOUBLE PRECISION;
    user_lon DOUBLE PRECISION;
    categories TEXT[] := ARRAY['academico', 'hogar', 'otros', 'deporte'];
    category_index INT;
BEGIN
    FOR i IN 1..200 LOOP
        -- Retrieve username and coordinates for each user
        SELECT username, latitud, longitud INTO current_username, user_lat, user_lon
        FROM usuarios
        WHERE format('debug_user_%s', i) = username;

        -- Insert two requests with random categories
        FOR j IN 1..2 LOOP
            category_index := (random() * 4)::INT;
            INSERT INTO peticion_servicio (
                username,
                titulo,
                peticion,
                descripcion,
                precio,
                fecha,
                latitud,
                longitud,
                categorias
            ) VALUES (
                current_username,
                format('Petición %s del usuario %s', j, current_username),
                TRUE,
                format('Descripción de la petición %s del usuario %s', j, current_username),
                random() * 100 + 10, -- Random price between 10 and 110
                CURRENT_DATE,--dia de hoy timestamp
                user_lat,
                user_lon,
                categories[category_index + 1]
            );
        END LOOP;

        -- Insert one service with a random category
        category_index := (random() * 4)::INT;
        INSERT INTO peticion_servicio (
            username,
            titulo,
            peticion,
            descripcion,
            precio,
            fecha,
            latitud,
            longitud,
            categorias
        ) VALUES (
            current_username,
            format('Servicio del usuario %s', current_username),
            FALSE,
            format('Descripción del servicio del usuario %s para debug', current_username),
            random() * 100 + 10, -- Random price between 10 and 110
            NOW()::DATE,
            user_lat,
            user_lon,
            categories[category_index + 1]
        );
    END LOOP;
END $$;

