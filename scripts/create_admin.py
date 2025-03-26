import asyncio
import sys
sys.path.append(".")  # Добавляем текущую директорию в PYTHONPATH

from app.database import async_session
from users.services import create_user, get_user_by_email
from media.models import MediaFile
from codes.models import AccessCode

async def create_admin_user(email: str, password: str) -> None:
    async with async_session() as session:
        # Проверяем, существует ли пользователь
        existing_user = await get_user_by_email(email, session)
        if existing_user:
            print(f"Пользователь с email {email} уже существует!")
            return

        # Создаем администратора
        await create_user(
            db=session,
            email=email,
            password=password,
            is_admin=True
        )
        print(f"Администратор успешно создан! Email: {email}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Использование: python scripts/create_admin.py email password")
        sys.exit(1)
    
    email = sys.argv[1]
    password = sys.argv[2]
    
    asyncio.run(create_admin_user(email, password)) 