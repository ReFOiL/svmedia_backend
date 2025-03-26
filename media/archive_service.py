import io
import zipfile
from app.core.config import settings
from aiobotocore.session import get_session
from aiobotocore.client import AioBaseClient
from typing import AsyncGenerator
from contextlib import asynccontextmanager


class ArchiveService:
    def __init__(self) -> None:
        self.session = get_session()

    @asynccontextmanager
    async def get_client(self) -> AsyncGenerator[AioBaseClient, None]:
        async with self.session.create_client(
            's3',
            endpoint_url=settings.AWS_ENDPOINT_URL,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            verify=False  # Отключаем проверку SSL для Selectel
        ) as client:
            yield client

    async def create_squad_archive(self, shift_number: int, squad_number: int) -> tuple[bytes, str]:
        """
        Создает ZIP-архив с фотографиями отряда и общими фотографиями смены
        
        Args:
            shift_number: номер смены
            squad_number: номер отряда
            
        Returns:
            tuple[bytes, str]: (содержимое архива, имя файла)
        """
        # Создаем ZIP-архив в памяти
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Получаем файлы из папки отряда
            squad_prefix = f"{shift_number}/{squad_number}/"
            print(f'<<< {settings.AWS_ENDPOINT_URL}, {settings.AWS_ACCESS_KEY_ID}, {settings.AWS_SECRET_ACCESS_KEY}')
            async with self.get_client() as client:
                squad_objects = await client.list_objects(
                    Bucket=settings.S3_BUCKET,
                    Prefix=squad_prefix
                )
            
            for obj in squad_objects.get('Contents', []):
                if obj['Key'].endswith('/'):  # Пропускаем папки
                    continue
                    
                # Получаем содержимое файла
                response = await client.get_object(
                    Bucket=settings.S3_BUCKET,
                    Key=obj['Key']
                )
                file_content = await response['Body'].read()
                
                # Добавляем файл в архив
                file_name = obj['Key'].split('/')[-1]
                zip_file.writestr(f"Отряд {squad_number}/{file_name}", file_content)
            
            # Получаем файлы из общей папки смены
            total_prefix = f"{shift_number}/total/"
            async with self.get_client() as client:
                total_objects = await client.list_objects(
                    Bucket=settings.S3_BUCKET,
                    Prefix=total_prefix
                )
                
                for obj in total_objects.get('Contents', []):
                    if obj['Key'].endswith('/'):  # Пропускаем папки
                        continue
                        
                    # Получаем содержимое файла
                    response = await client.get_object(
                        Bucket=settings.S3_BUCKET,
                        Key=obj['Key']
                    )
                    file_content = await response['Body'].read()
                    
                    # Добавляем файл в архив
                    file_name = obj['Key'].split('/')[-1]
                    zip_file.writestr(f"Общие фото/{file_name}", file_content)
        
        # Получаем содержимое архива
        archive_content = zip_buffer.getvalue()
        archive_name = f"shift_{shift_number}_squad_{squad_number}.zip"
        
        return archive_content, archive_name

archive_service = ArchiveService() 