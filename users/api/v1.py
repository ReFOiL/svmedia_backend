from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependency import get_db
from users.services import (
    authenticate_user,
    create_access_token,
    get_current_user,
    create_user,
    get_user_by_email
)
from users.schemas import Token, UserCreate, UserResponse
from app.core.config import settings

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    Аутентификация пользователя и получение токена доступа.
    """
    user = await authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@router.post("/create", response_model=UserResponse)
async def create_new_user(
    user_data: UserCreate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Создание нового пользователя (только для администраторов).
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только администраторы могут создавать новых пользователей"
        )
    
    # Проверяем, не существует ли уже пользователь с таким email
    existing_user = await get_user_by_email(user_data.email, db)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким email уже существует"
        )
    
    user = await create_user(
        db=db,
        email=user_data.email,
        password=user_data.password,
        is_admin=user_data.is_admin
    )
    
    return user

@router.get("/me", response_model=UserResponse)
async def read_users_me(
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Получение информации о текущем пользователе.
    """
    return current_user 