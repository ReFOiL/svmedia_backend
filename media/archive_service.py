import logging
from app.core.config import settings
from aiobotocore.session import get_session  # type: ignore
from aiobotocore.client import AioBaseClient  # type: ignore
from typing import AsyncGenerator
from contextlib import asynccontextmanager
from botocore.config import Config  # type: ignore

logger = logging.getLogger(__name__)

class ArchiveService:
    def __init__(self) -> None:
        self.session = get_session()

    @asynccontextmanager
    async def get_client(self) -> AsyncGenerator[AioBaseClient, None]:
        config = Config(
            s3={'addressing_style': 'path'},
            signature_version='s3v4'
        )
        
        async with self.session.create_client(
            's3',
            endpoint_url=settings.AWS_ENDPOINT_URL,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name='ru-7',
            verify=False,
            config=config
        ) as client:
            yield client

    async def generate_download_url(self, shift_number: int, squad_number: int) -> str:
        """
        Генерирует временную ссылку для скачивания архива
        :param shift_number: Номер смены
        :param squad_number: Номер отряда
        :return: Временная ссылка для скачивания
        """
        archive_key = f"shifts/{shift_number}_{squad_number}.zip"
        
        async with self.get_client() as client:
            try:
                # Проверяем существование файла
                await client.head_object(
                    Bucket=settings.AWS_BUCKET_NAME,
                    Key=archive_key
                )
                
                # Генерируем временную ссылку
                url = await client.generate_presigned_url(
                    'get_object',
                    Params={
                        'Bucket': settings.AWS_BUCKET_NAME,
                        'Key': archive_key
                    },
                    ExpiresIn=86400  # Ссылка действительна 24 часа
                )
                return url
            except Exception as e:
                logger.error(f"Error generating download URL for {archive_key}: {str(e)}")
                raise Exception(f"Архив не найден или произошла ошибка при генерации ссылки: {str(e)}")

archive_service = ArchiveService() 