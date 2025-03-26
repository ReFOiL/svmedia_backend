import secrets
import string
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert
from codes.models import AccessCode
from users.models import User

class CodeGenerator:
    def __init__(self, length: int = 8):
        self.length = length
        self.alphabet = string.ascii_letters + string.digits

    def generate_code(self) -> str:
        """Generate a single unique code"""
        return ''.join(secrets.choice(self.alphabet) for _ in range(self.length))

    async def generate_multiple_codes(
        self, 
        count: int, 
        user: User, 
        db: AsyncSession,
        squad_number: int,
        shift_number: int
    ) -> List[AccessCode]:
        """Generate multiple unique codes and save them to database"""
        # Генерируем коды с запасом на случай дубликатов
        codes: set[str] = set()
        max_attempts = count * 2  # Увеличиваем количество попыток для учета возможных дубликатов
        
        while len(codes) < count and len(codes) < max_attempts:
            codes.add(self.generate_code())
        
        if len(codes) < count:
            raise ValueError(f"Не удалось сгенерировать {count} уникальных кодов после {max_attempts} попыток")
        
        # Подготавливаем данные для bulk insert
        codes_data = [
            {
                "code": code, 
                "created_by_id": user.id,
                "squad_number": squad_number,
                "shift_number": shift_number
            }
            for code in codes
        ]
        
        # Выполняем bulk insert
        result = await db.execute(
            insert(AccessCode).returning(AccessCode),
            codes_data
        )
        await db.commit()
        
        # Получаем созданные коды
        db_codes = list(result.scalars().all())
        return db_codes

    async def is_code_unique(self, code: str, db: AsyncSession) -> bool:
        """Check if a code is unique in the database"""
        result = await db.execute(
            select(AccessCode).where(AccessCode.code == code)
        )
        return result.scalar_one_or_none() is None

code_generator = CodeGenerator() 