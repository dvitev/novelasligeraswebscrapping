# Stage 1: Dependencies
FROM python:3.12-slim AS deps

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/
RUN pip install --no-cache-dir --target=/app/packages -r requirements.txt

# Stage 2: Development
FROM deps AS dev

WORKDIR /app

COPY --from=deps /app/packages /app/packages
ENV PYTHONPATH=/app/packages

COPY . /app/

RUN mkdir -p /app/static/images /app/static/pdf /app/static/epub /app/static/fonts
RUN chmod -R 755 /app/static

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

# Stage 3: Production
FROM python:3.12-slim AS production

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    gunicorn \
    && rm -rf /var/lib/apt/lists/*

COPY --from=deps /app/packages /app/packages
ENV PYTHONPATH=/app/packages

COPY . /app/

RUN mkdir -p /app/static/images /app/static/pdf /app/static/epub /app/static/fonts && \
    chmod -R 755 /app/static

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health/')" || exit 1

USER nobody

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-", "recopilarnovelasdjango.wsgi:application"]