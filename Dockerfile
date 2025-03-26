# syntax=docker/dockerfile:1.4

# Этап сборки зависимостей
FROM python:3.12-slim as builder

# Устанавливаем build-time зависимости
RUN rm -f /var/lib/apt/lists/lock \
    /var/cache/apt/archives/lock \
    /var/lib/dpkg/lock* \
    && apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.docker.txt .
RUN pip install --no-cache-dir -r requirements.docker.txt

# Финальный этап
FROM python:3.12-slim

# Устанавливаем runtime зависимости
RUN rm -f /var/lib/apt/lists/lock \
    /var/cache/apt/archives/lock \
    /var/lib/dpkg/lock* \
    && apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    curl \
    ca-certificates \
    openssl \
    && rm -rf /var/lib/apt/lists/*

# Копируем установленные пакеты из builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

WORKDIR /app

# Копируем код приложения
COPY . .

# Добавляем текущую директорию в PYTHONPATH
ENV PYTHONPATH=/app

# Проверка работоспособности
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Используем python для запуска uvicorn
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
