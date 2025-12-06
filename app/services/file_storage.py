import json
import logging
import time
from pathlib import Path
from typing import Optional
from uuid import uuid4

from fastapi import UploadFile

from app.models.entity_model import SensitiveEntity
from app.models.processing_result import ProcessingResult

logger = logging.getLogger(__name__)


class FileStorageService:
    def __init__(self, temp_dir: Path):
        self.temp_dir = temp_dir
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def save_upload(self, upload: UploadFile) -> tuple[str, Path]:
        file_id = uuid4().hex
        safe_name = Path(upload.filename or "upload").name
        target = self.temp_dir / f"{file_id}_{safe_name}"

        with target.open("wb") as buffer:
            upload.file.seek(0)
            buffer.write(upload.file.read())

        return file_id, target

    def save_result(self, result: ProcessingResult) -> None:
        meta_path = self._metadata_path(result.file_id)
        payload = {
            "file_id": result.file_id,
            "original_filename": result.original_filename,
            "uploaded_path": str(result.uploaded_path),
            "masked_path": str(result.masked_path),
            "full_text": result.full_text,
            "masked_text": result.masked_text,
            "entities": [vars(entity) for entity in result.entities],
            "gpt_logs": result.gpt_logs,
        }
        meta_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    def load_result(self, file_id: str) -> Optional[ProcessingResult]:
        meta_path = self._metadata_path(file_id)
        if not meta_path.exists():
            return None

        data = json.loads(meta_path.read_text(encoding="utf-8"))
        entities = [
            SensitiveEntity(
                type=item.get("type", ""),
                text=item.get("text", ""),
                start=int(item.get("start", 0)),
                end=int(item.get("end", 0)),
            )
            for item in data.get("entities", [])
        ]

        return ProcessingResult(
            file_id=data["file_id"],
            original_filename=data["original_filename"],
            uploaded_path=Path(data["uploaded_path"]),
            masked_path=Path(data["masked_path"]),
            full_text=data["full_text"],
            masked_text=data["masked_text"],
            entities=entities,
            gpt_logs=data.get("gpt_logs", []),
        )

    def cleanup(self, max_age_seconds: int = 60 * 60 * 24) -> None:
        now = time.time()
        for path in self.temp_dir.glob("*"):
            try:
                if now - path.stat().st_mtime > max_age_seconds:
                    path.unlink(missing_ok=True)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Cleanup skipped for %s: %s", path, exc)

    def _metadata_path(self, file_id: str) -> Path:
        return self.temp_dir / f"{file_id}.json"
