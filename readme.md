# Novelas Ligeras - Web Scraping Project

Plataforma de novels ligeras con Django backend + Next.js frontend.

## Proyectos

```
novelasligeraswebscrapping/
├── recopilarnovelasdjango/   # Backend (Django REST API)
├── recopilarnovelasnextjs/   # Frontend (Next.js 14)
├── scripts/                  # Utilidades Docker
├── docker-compose.yml        # Orquestación completa
├── mongod.conf              # Config MongoDB
├── .env / .env.example      # Variables de entorno
└── readme.md
```

## Quick Start

```bash
# 1. Copiar configuración
cp .env.example .env

# 2. Levantar servicios
docker-compose up -d

# 3. Verificar
curl http://localhost:8000/api/health/
curl http://localhost:3000
```

## Servicios

| Servicio | Puerto | Descripción |
|----------|--------|-------------|
| API Django | 8000 | REST API con MongoDB |
| Frontend | 3000 | Next.js app |
| MongoDB | 27017 | Base de datos |
| Redis | 6379 | Cache + Celery broker |

## Producción - Django API

### Gunicorn (reemplazar runserver)

```dockerfile
# Dockerfile
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "120", "recopilarnovelasdjango.wsgi:application"]
```

### Variables de entorno críticas

```bash
DJANGO_SECRET_KEY=<clave-segura-32+-caracteres>
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=tudominio.com
CORS_ALLOWED_ORIGINS=https://tudominio.com
```

### HTTPS con Nginx

```yaml
# docker-compose.yml
nginx:
  image: nginx:alpine
  ports:
    - "80:80"
    - "443:443"
  volumes:
    - ./nginx.conf:/etc/nginx/nginx.conf:ro
  depends_on:
    - api
    - frontend
```

### Rate Limiting (Nginx)

```nginx
# nginx.conf
http {
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

    server {
        location /api/ {
            limit_req zone=api_limit burst=20 nodelay;
        }
    }
}
```

## Producción - Next.js Frontend

### Build standalone (reduce ~800MB → ~150MB)

```javascript
// next.config.mjs
export default {
  output: 'standalone',
}
```

### Variables producción

```bash
API_URL=https://api.tudominio.com
```

### Docker multistage

```dockerfile
# recopilarnovelasnextjs/Dockerfile
FROM node:18-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

FROM node:18-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

FROM node:18-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
EXPOSE 3000
CMD ["node", "server.js"]
```

## Scripts de utilidad

```bash
./scripts/start-dev.sh      # Levantar servicios desarrollo
./scripts/backup-mongodb.sh # Backup MongoDB
./scripts/restore-mongodb.sh # Restaurar backup
./scripts/logs.sh           # Ver logs (servicio opcional)
```

## API Endpoints

- `GET /api/sitios/` - Lista de sitios
- `GET /api/novelas/<sitio_id>/` - Novelas por sitio
- `GET /api/capitulos/<novela_id>/` - Capítulos por novela
- `GET /api/contenido/<capitulo_id>/` - Contenido capítulo
- `GET /api/generos/<sitio_id>/` - Géneros únicos
- `GET /api/conteocapitulosnovela/<novela_id>/` - Conteo capítulos
- `GET /api/health/` - Health check

## Desarrollo

```bash
# Backend
cd recopilarnovelasdjango
pip install -r requirements.txt
python manage.py runserver

# Frontend
cd recopilarnovelasnextjs
npm install
npm run dev
```

## Licencia

GNU LESSER GENERAL PUBLIC LICENSE