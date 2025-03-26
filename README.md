# SVMedia Backend

Бэкенд-сервис для SVMedia, построенный на FastAPI.

## Технологический стек

- **FastAPI** - современный веб-фреймворк для создания API
- **PostgreSQL** - надежная реляционная база данных
- **MinIO** - S3-совместимое объектное хранилище
- **SQLAlchemy** - ORM для работы с базой данных
- **Alembic** - инструмент для миграций базы данных
- **Pydantic** - валидация данных и сериализация
- **Docker** - контейнеризация приложения
- **JWT** - аутентификация и авторизация

## Требования

- Docker
- Docker Compose
- Python 3.12+
- Git
- [uv](https://github.com/astral-sh/uv) - современный, быстрый менеджер пакетов Python

## Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/yourusername/svmedia-backend.git
cd svmedia-backend
```

2. Создайте виртуальное окружение с помощью uv:
```bash
uv venv
```

3. Активируйте виртуальное окружение:
```bash
# Windows
.venv\Scripts\activate

# Linux/macOS
source .venv/bin/activate
```

4. Установите зависимости:
```bash
# Основные зависимости
uv install

# Зависимости для разработки
uv install --dev
```

## Настройка окружения

1. Скопируйте файл `.env.example` в `.env`:
```bash
cp .env.example .env
```

2. Отредактируйте `.env` файл, указав необходимые значения:
- Настройки базы данных PostgreSQL
- Настройки AWS S3 или MinIO
- Секретный ключ и другие параметры безопасности

## Запуск

### Режим разработки

```bash
uvicorn app.main:app --reload
```

### Продакшн режим

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Разработка

### Форматирование кода

```bash
# Форматирование с помощью black
black .

# Сортировка импортов
isort .
```

### Проверка типов

```bash
mypy .
```

### Запуск тестов

```bash
pytest
```

### Миграции базы данных

```bash
# Создание новой миграции
alembic revision --autogenerate -m "описание изменений"

# Применение миграций
alembic upgrade head
```

## Docker

Для запуска в Docker:

```bash
docker-compose up -d
```

## Документация API

После запуска сервера документация доступна по адресам:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Работа с базой данных

### Доступ через pgAdmin

1. Откройте http://localhost:5050 в браузере
2. Войдите используя:
   - Email: `admin@admin.com`
   - Пароль: `admin`
3. Добавьте новый сервер:
   - Name: `SVMedia DB` (или любое другое)
   - Host: `db`
   - Port: `5432`
   - Database: `svmedia`
   - Username: `postgres`
   - Password: `postgres`

### Управление миграциями

Все команды для работы с миграциями выполняются через Docker Compose:

1. Создание новой миграции:
```bash
docker compose run --rm alembic alembic revision --autogenerate -m "название_миграции"
```

2. Применение всех миграций:
```bash
docker compose run --rm alembic
```

3. Откат на одну миграцию назад:
```bash
docker compose run --rm alembic alembic downgrade -1
```

4. Просмотр истории миграций:
```bash
docker compose run --rm alembic alembic history
```

5. Просмотр текущей версии базы данных:
```bash
docker compose run --rm alembic alembic current
```

## Тестирование

### Запуск тестов

```bash
# Запуск всех тестов
pytest

# Запуск с отчетом о покрытии
pytest --cov=app

# Запуск конкретного теста
pytest tests/test_api/test_users.py -v

# Запуск тестов в Docker
docker compose run --rm backend pytest
```

### Линтеры и форматтеры

```bash
# Проверка типов
mypy app

# Форматирование кода
black app tests

# Проверка стиля
flake8 app tests

# Сортировка импортов
isort app tests
```

## Безопасность

1. **Аутентификация**:
   - JWT токены для авторизации
   - Настраиваемое время жизни токенов
   - Безопасное хранение паролей (bcrypt)

2. **Хранение данных**:
   - Все секреты в переменных окружения
   - Безопасное хранение файлов в MinIO/S3
   - Одноразовые ссылки на файлы

3. **API безопасность**:
   - CORS защита
   - Rate limiting
   - Валидация входных данных

## Деплой

### Подготовка к продакшену

1. Измените переменные окружения:
   - Установите сложные пароли
   - Настройте CORS_ORIGINS
   - Установите безопасный SECRET_KEY

2. Настройте SSL/TLS:
   - Добавьте HTTPS через reverse proxy
   - Настройте автоматическое обновление сертификатов

3. Настройте бэкапы:
   - Регулярное резервное копирование базы данных
   - Бэкап файлов из MinIO/S3

### Мониторинг

- Prometheus для метрик
- Grafana для визуализации
- Sentry для отслеживания ошибок

## Структура проекта

```
backend/
├── alembic/          # Миграции базы данных
├── app/              # Основной код приложения
│   ├── api/         # API endpoints
│   ├── core/        # Основные настройки
│   ├── crud/        # CRUD операции
│   ├── db/          # Модели базы данных
│   ├── schemas/     # Pydantic модели
│   └── services/    # Бизнес-логика
├── tests/            # Тесты
├── .env              # Переменные окружения
├── .env.example      # Пример переменных окружения
├── requirements.txt  # Зависимости
└── docker-compose.yml # Конфигурация Docker
```

## Лицензия

MIT

## Поддержка

При возникновении проблем:
1. Проверьте [известные проблемы](issues)
2. Создайте новый issue с подробным описанием проблемы
3. Приложите логи и конфигурацию (без секретных данных) 