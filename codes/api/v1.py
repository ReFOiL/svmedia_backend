from typing import List, Sequence
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from app.dependency import get_db
from users.services import get_current_user
from users.models import User
from codes.models import AccessCode
from codes.schemas import (
    AccessCodeResponse,
    AccessCodeList,
    FormData
)
from codes.services import code_generator
from media.archive_service import archive_service
from datetime import datetime, timezone

router = APIRouter(prefix="/codes", tags=["codes"])

@router.post("/generate", response_model=List[AccessCodeResponse])
async def generate_codes(
    count: int = Query(..., gt=0),
    squad_number: int = Query(..., gt=0),
    shift_number: int = Query(..., gt=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[AccessCode]:
    """
    Генерирует указанное количество уникальных кодов доступа.
    Только для администраторов.
    
    Args:
        count: количество генерируемых кодов
        squad_number: номер отряда
        shift_number: номер смены
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=403,
            detail="Только администраторы могут генерировать коды"
        )
    
    codes = await code_generator.generate_multiple_codes(
        count=count,
        user=current_user,
        db=db,
        squad_number=squad_number,
        shift_number=shift_number
    )
    return codes

@router.get("/", response_model=AccessCodeList)
async def list_codes(
    skip: int = 0,
    limit: int = 100,
    search: str | None = None,
    is_used: bool | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> dict[str, Sequence[AccessCode] | int | None]:
    """
    Получает список всех кодов с возможностью фильтрации и поиска.
    Только для администраторов.
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=403,
            detail="Только администраторы могут просматривать коды"
        )
    
    query = select(AccessCode)
    
    if search:
        query = query.where(
            (AccessCode.code.ilike(f"%{search}%")) |
            (AccessCode.full_name.ilike(f"%{search}%"))
        )
    
    if is_used is not None:
        query = query.where(AccessCode.is_used == is_used)
    
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    codes = result.scalars().all()
    
    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    
    return {
        "items": codes,
        "total": total,
        "skip": skip,
        "limit": limit
    }

@router.get("/{code}/usage", response_model=AccessCodeResponse)
async def get_code_usage(
    code: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> AccessCode:
    """
    Получает информацию об использовании конкретного кода.
    Только для администраторов.
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=403,
            detail="Только администраторы могут просматривать использование кодов"
        )
    
    result = await db.execute(
        select(AccessCode).where(AccessCode.code == code)
    )
    access_code = result.scalar_one_or_none()
    
    if not access_code:
        raise HTTPException(
            status_code=404,
            detail="Код не найден"
        )
    
    return access_code

@router.post("/{code}/use")
async def use_code(
    code: str,
    form_data: FormData,
    db: AsyncSession = Depends(get_db)
) -> Response:
    """
    Использует код доступа и возвращает архив с фотографиями.
    Проверяет соответствие кода смене и отряду.
    """
    # Ищем код в базе данных
    result = await db.execute(
        select(AccessCode).where(
            and_(
                AccessCode.code == code,
                AccessCode.shift_number == int(form_data.shift),
                AccessCode.squad_number == int(form_data.group)
            )
        )
    )
    access_code = result.scalar_one_or_none()
    
    if not access_code:
        raise HTTPException(
            status_code=404,
            detail="Код не найден или не соответствует указанной смене/отряду"
        )
    
    if access_code.is_used:
        raise HTTPException(
            status_code=400,
            detail="Этот код уже был использован"
        )
    
    # Обновляем данные использования кода
    access_code.is_used = True
    access_code.used_at = datetime.now(timezone.utc)  # type: ignore
    access_code.full_name = f"{form_data.name} {form_data.surname}"
    access_code.usage_data = form_data.model_dump()
    
    await db.commit()
    await db.refresh(access_code)
    
    # Создаем архив с фотографиями
    archive_content, archive_name = await archive_service.create_squad_archive(
        shift_number=access_code.shift_number,
        squad_number=access_code.squad_number
    )
    
    return Response(
        content=archive_content,
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename={archive_name}"
        }
    ) 