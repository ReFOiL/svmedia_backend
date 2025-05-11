import logging
from app.core.config import settings
from aiobotocore.session import get_session  # type: ignore
from aiobotocore.client import AioBaseClient  # type: ignore
from typing import AsyncGenerator, Literal, Dict
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

    async def generate_download_urls(self, shift_number: int, squad_number: int) -> Dict[str, str]:
        """
        Генерирует временные ссылки для скачивания обоих архивов
        :param shift_number: Номер смены
        :param squad_number: Номер отряда
        :return: Словарь с ссылками на архивы
        """
        squad_archive_key = f"shifts/{shift_number}_{squad_number}.zip"
        total_archive_key = f"shifts/{shift_number}_total.zip"
        
        async with self.get_client() as client:
            try:
                # Проверяем существование файлов
                await client.head_object(
                    Bucket=settings.AWS_BUCKET_NAME,
                    Key=squad_archive_key
                )
                await client.head_object(
                    Bucket=settings.AWS_BUCKET_NAME,
                    Key=total_archive_key
                )
                
                # Генерируем временные ссылки
                squad_url = await client.generate_presigned_url(
                    'get_object',
                    Params={
                        'Bucket': settings.AWS_BUCKET_NAME,
                        'Key': squad_archive_key
                    },
                    ExpiresIn=86400  # Ссылка действительна 24 часа
                )
                logger.info(f"Generated squad archive URL: {squad_url}")
                
                total_url = await client.generate_presigned_url(
                    'get_object',
                    Params={
                        'Bucket': settings.AWS_BUCKET_NAME,
                        'Key': total_archive_key
                    },
                    ExpiresIn=86400  # Ссылка действительна 24 часа
                )
                logger.info(f"Generated total archive URL: {total_url}")
                
                result = {
                    "squad_archive": squad_url,
                    "total_archive": total_url
                }
                logger.info(f"Returning URLs: {result}")
                return result
            except Exception as e:
                logger.error(f"Error generating download URLs: {str(e)}")
                raise Exception(f"Архивы не найдены или произошла ошибка при генерации ссылок: {str(e)}")

archive_service = ArchiveService() 