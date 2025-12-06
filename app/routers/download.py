from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from starlette import status

from app.dependencies import get_storage
from app.services.file_storage import FileStorageService

router = APIRouter()


@router.get("/download/{file_id}")
async def download(file_id: str, storage: FileStorageService = Depends(get_storage)):
    result = storage.load_result(file_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Файл не найден")

    filename = f"{result.original_filename.rsplit('.', 1)[0]}_masked{result.masked_path.suffix}"
    return FileResponse(
        path=result.masked_path,
        filename=filename,
        media_type="application/octet-stream",
    )
