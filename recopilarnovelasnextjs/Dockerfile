# Utiliza la imagen base de Node.js
FROM node:20.11.1

# Crea el directorio de la aplicación
WORKDIR /app

# Copia los archivos del proyecto
COPY . /app

# Instala las dependencias
RUN npm install

# Construye la aplicación Next.js
# RUN npm run build

# Expone el puerto 3000
EXPOSE 3000

# Inicia la aplicación Next.js
CMD ["npm", "run", "dev"]