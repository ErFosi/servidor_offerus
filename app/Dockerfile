# Usar una imagen oficial de Python como imagen base
FROM python:3.10

# Establecer el directorio de trabajo en el contenedor
WORKDIR /code

# Copiar los requerimientos e instalar las dependencias del proyecto
COPY ./api/requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Copiar el resto del código de la aplicación
COPY ./api /code

# Comando para ejecutar la aplicación usando Uvicorn
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--reload"]
