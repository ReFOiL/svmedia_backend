from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from users.api.v1 import router as users_router
from codes.api.v1 import router as codes_router
from media.api.v1 import router as media_router

def configure_app(application: FastAPI) -> None:
    # Настройка CORS
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # В продакшене заменить на конкретные домены
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Подключаем роутеры
    application.include_router(users_router, prefix="/api")
    application.include_router(codes_router, prefix="/api")
    application.include_router(media_router, prefix="/api")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API SVMedia",
    version="1.0.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json"
)

configure_app(app)

@app.get("/")
async def root() -> dict:
    return {
        "message": "Добро пожаловать в API SVMedia",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check() -> dict:
    return {
        "status": "healthy",
        "version": "1.0.0"
    }
