import zipstream
import asyncio
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

    async def _s3_stream_for_key(self, key, chunk_size=1024*1024):
        async with self.get_client() as client:
            response = await client.get_object(
                Bucket=settings.S3_BUCKET,
                Key=key
            )
            stream = response['Body']
            while True:
                chunk = await stream.read(chunk_size)
                if not chunk:
                    break
                yield chunk

    def async_to_sync_iter(self, async_gen):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        agen = async_gen.__aiter__()
        try:
            while True:
                try:
                    chunk = loop.run_until_complete(agen.__anext__())
                    yield chunk
                except StopAsyncIteration:
                    break
        finally:
            loop.close()

    async def stream_squad_archive(self, shift_number: int, squad_number: int):
        z = zipstream.ZipStream()
        # Файлы отряда
        squad_prefix = f"{shift_number}/{squad_number}/"
        async with self.get_client() as client:
            squad_objects = await client.list_objects(
                Bucket=settings.S3_BUCKET,
                Prefix=squad_prefix
            )
            for obj in squad_objects.get('Contents', []):
                if obj['Key'].endswith('/'):
                    continue
                file_name = obj['Key'].split('/')[-1]
                arcname = f"Отряд {squad_number}/{file_name}"
                z.add(arcname=arcname, data=self.async_to_sync_iter(self._s3_stream_for_key(obj['Key'])))
        # Общие файлы смены
        total_prefix = f"{shift_number}/total/"
        async with self.get_client() as client:
            total_objects = await client.list_objects(
                Bucket=settings.S3_BUCKET,
                Prefix=total_prefix
            )
            for obj in total_objects.get('Contents', []):
                if obj['Key'].endswith('/'):
                    continue
                file_name = obj['Key'].split('/')[-1]
                arcname = f"Общие фото/{file_name}"
                z.add(arcname=arcname, data=self.async_to_sync_iter(self._s3_stream_for_key(obj['Key'])))
        archive_name = f"shift_{shift_number}_squad_{squad_number}.zip"
        return z, archive_name

archive_service = ArchiveService() 