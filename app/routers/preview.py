from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from starlette import status
from starlette.templating import Jinja2Templates

from app.dependencies import get_settings, get_storage
from app.services import masking
from app.services.file_storage import FileStorageService

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/preview/{file_id}", response_class=HTMLResponse)
async def preview(
    request: Request,
    file_id: str,
    storage: FileStorageService = Depends(get_storage),
    settings=Depends(get_settings),
):
    result = storage.load_result(file_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Файл не найден")

    highlighted = masking.highlight_text(result.full_text, result.entities)

    return templates.TemplateResponse(
        "preview.html",
        {
            "request": request,
            "file_id": file_id,
            "original_filename": result.original_filename,
            "entities": result.entities,
            "highlighted_text": highlighted,
            "mask_style": settings.mask_style,
            "gpt_logs": result.gpt_logs,
        },
    )
