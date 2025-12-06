from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any

from app.models.entity_model import SensitiveEntity


@dataclass
class ProcessingResult:
    file_id: str
    original_filename: str
    uploaded_path: Path
    masked_path: Path
    full_text: str
    masked_text: str
    entities: List[SensitiveEntity]
    gpt_logs: List[Dict[str, Any]]
