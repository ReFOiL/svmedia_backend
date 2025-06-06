from typing import List, Sequence
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse, PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, not_
from app.dependency import get_db
from users.services import get_current_user
from users.models import User
from codes.models import AccessCode
from codes.schemas import (
    AccessCodeResponse,
    AccessCodeList,
    FormData,
    ShiftPromocodesResponse,
    SquadPromocodes
)
from codes.services import code_generator
from media.archive_service import archive_service
from datetime import datetime, timezone
import logging

router = APIRouter(prefix="/codes", tags=["codes"])

logger = logging.getLogger(__name__)

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
) -> dict:
    """
    Использует код доступа и возвращает временные ссылки на архивы с фотографиями.
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
    
    # Генерируем временные ссылки на скачивание
    try:
        download_urls = await archive_service.generate_download_urls(
            shift_number=access_code.shift_number,
            squad_number=access_code.squad_number
        )
        logger.info(f"Generated download URLs: {download_urls}")
        await db.commit()
        await db.refresh(access_code)
        
        # Создаем HTML страницу для автоматического скачивания
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Скачивание архивов</title>
            <meta charset="utf-8">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    text-align: center;
                    padding: 20px;
                }}
                .message {{
                    margin: 20px 0;
                    padding: 10px;
                    border-radius: 5px;
                }}
                .success {{
                    background-color: #d4edda;
                    color: #155724;
                }}
                .error {{
                    background-color: #f8d7da;
                    color: #721c24;
                }}
            </style>
        </head>
        <body>
            <h1>Скачивание архивов</h1>
            <div class="message success">
                Начинаем скачивание архивов...
            </div>
            <script>
                // Функция для скачивания файла
                function downloadFile(url, filename) {{
                    const link = document.createElement('a');
                    link.href = url;
                    link.download = filename;
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);
                }}

                // Скачиваем оба архива
                window.onload = function() {{
                    downloadFile('{download_urls["squad_archive"]}', 'archive_squad.zip');
                    setTimeout(() => {{
                        downloadFile('{download_urls["total_archive"]}', 'archive_total.zip');
                    }}, 1000);
                }};
            </script>
        </body>
        </html>
        """
        
        return HTMLResponse(content=html_content)
    except Exception as e:
        logger.error(f"Error generating download URLs: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@router.get("/shift/{shift_number}", response_model=ShiftPromocodesResponse)
async def get_shift_promocodes(
    shift_number: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ShiftPromocodesResponse:
    """
    Получает все промокоды для указанной смены, сгруппированные по отрядам.
    Только для администраторов.
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=403,
            detail="Только администраторы могут просматривать промокоды"
        )
    
    # Получаем все промокоды для указанной смены
    result = await db.execute(
        select(AccessCode)
        .where(AccessCode.shift_number == shift_number)
        .order_by(AccessCode.squad_number)
    )
    codes = result.scalars().all()
    
    # Группируем промокоды по отрядам
    squads_dict = {}
    for code in codes:
        if code.squad_number not in squads_dict:
            squads_dict[code.squad_number] = []
        squads_dict[code.squad_number].append(code)
    
    # Формируем ответ
    squads = [
        SquadPromocodes(
            squad_number=squad_number,
            promocodes=codes
        )
        for squad_number, codes in sorted(squads_dict.items())
    ]
    
    return ShiftPromocodesResponse(
        shift_number=shift_number,
        squads=squads
    )

@router.get("/shift/{shift_number}/print", response_class=PlainTextResponse)
async def get_shift_promocodes_print(
    shift_number: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> str:
    """
    Получает все неактивированные промокоды для указанной смены в текстовом формате для печати.
    Только для администраторов.
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=403,
            detail="Только администраторы могут просматривать промокоды"
        )
    
    # Получаем все неактивированные промокоды для указанной смены
    result = await db.execute(
        select(AccessCode)
        .where(
            and_(
                AccessCode.shift_number == shift_number,
                not_(AccessCode.is_used)
            )
        )
        .order_by(AccessCode.squad_number)
    )
    codes = result.scalars().all()
    
    # Группируем промокоды по отрядам
    squads_dict: dict[int, list[AccessCode]] = {}
    for code in codes:
        if code.squad_number not in squads_dict:
            squads_dict[code.squad_number] = []
        squads_dict[code.squad_number].append(code)
    
    # Формируем текстовый ответ
    output = []
    output.append(f"Смена {shift_number} - Неактивированные промокоды\n")
    output.append("=" * 50 + "\n")
    
    for squad_number in sorted(squads_dict.keys()):
        output.append(f"\nОтряд {squad_number}")
        output.append("-" * 30)
        
        for code in squads_dict[squad_number]:
            output.append(f"{code.code}")
        
        output.append("")  # Пустая строка между отрядами
    
    return "\n".join(output)
