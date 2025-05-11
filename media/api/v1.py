from fastapi import APIRouter, Depends, HTTPException
from app.core.config import settings
from media.archive_service import archive_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/media", tags=["media"])

@router.get("/check-total/{shift_number}")
async def check_total_folder(shift_number: int):
    """
    Проверяет содержимое папки total для указанной смены
    """
    total_prefix = f"{shift_number}/total/"
    async with archive_service.get_client() as client:
        try:
            total_objects = await client.list_objects(
                Bucket=settings.AWS_BUCKET_NAME,
                Prefix=total_prefix
            )
            files = []
            for obj in total_objects.get('Contents', []):
                files.append({
                    'key': obj['Key'],
                    'size': obj['Size'],
                    'last_modified': obj['LastModified'].isoformat()
                })
            return {
                'shift_number': shift_number,
                'total_files': len(files),
                'files': files
            }
        except Exception as e:
            logger.error(f"Error checking total folder: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error checking total folder: {str(e)}"
            )
