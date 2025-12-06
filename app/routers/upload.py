import logging
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette import status
from starlette.templating import Jinja2Templates

from app.dependencies import get_gpt_client, get_settings, get_storage
from app.models.entity_model import MaskingOptions
from app.models.processing_result import ProcessingResult
from app.services import document_parser, masking
from app.services.exporter import export_masked
from app.services.file_storage import FileStorageService
from app.services.yandex_gpt import YandexGPTClient

logger = logging.getLogger(__name__)

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def upload_form(request: Request, settings=Depends(get_settings)):
    return templates.TemplateResponse(
        "upload.html",
        {
            "request": request,
            "max_size_mb": settings.max_upload_size_mb,
        },
    )


@router.post("/upload")
async def upload_file(
    request: Request,
    upload: UploadFile = File(...),
    settings=Depends(get_settings),
    storage: FileStorageService = Depends(get_storage),
    gpt_client: YandexGPTClient = Depends(get_gpt_client),
):
    _validate_upload(upload, settings.max_upload_size_bytes)

    file_id, saved_path = storage.save_upload(upload)
    logger.info("Uploaded file saved to %s", saved_path)

    document = await run_in_threadpool(
        document_parser.parse_document, saved_path, upload.content_type, settings.ocr_lang
    )

    entities, gpt_logs = await gpt_client.detect_sensitive_data(document.full_text)
    options = MaskingOptions(style=settings.mask_style)
    masked = masking.mask_text(document.full_text, entities, options)
    masked_path = export_masked(masked, original_path=saved_path, target_dir=settings.temp_dir)

    result = ProcessingResult(
        file_id=file_id,
        original_filename=upload.filename or "document",
        uploaded_path=saved_path,
        masked_path=masked_path,
        full_text=document.full_text,
        masked_text=masked,
        entities=entities,
        gpt_logs=gpt_logs,
    )
    storage.save_result(result)

    return RedirectResponse(
        url=f"/preview/{file_id}",
        status_code=status.HTTP_303_SEE_OTHER,
    )


def _validate_upload(upload: UploadFile, max_size_bytes: int) -> None:
    filename = upload.filename or ""
    if not document_parser.is_supported(filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неподдерживаемый формат файла. Разрешены: docx, pdf, jpg, png, tiff.",
        )

    upload.file.seek(0, 2)
    size = upload.file.tell()
    upload.file.seek(0)

    if size > max_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Файл превышает максимальный размер загрузки.",
        )
