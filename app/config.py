import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass
class Settings:
    yandex_gpt_api_key: str
    yandex_gpt_api_url: str
    yandex_gpt_model_uri: str = ""
    yandex_folder_id: str = ""
    yandex_iam_token: str = ""
    ocr_lang: str = "rus+eng"
    max_upload_size_mb: int = 50
    temp_dir: Path = Path("./temp")
    mask_style: str = "asterisks"
    chunk_size: int = 6000

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024


def load_settings() -> Settings:
    load_dotenv()
    return Settings(
        yandex_gpt_api_key=os.getenv("YANDEX_GPT_API_KEY", ""),
        yandex_gpt_api_url=os.getenv(
            "YANDEX_GPT_API_URL",
            "https://llm.api.cloud.yandex.net/foundationModels/v1/completion",
        ),
        yandex_gpt_model_uri=os.getenv("YANDEX_GPT_MODEL_URI", ""),
        yandex_folder_id=os.getenv("YANDEX_FOLDER_ID", ""),
        yandex_iam_token=os.getenv("YANDEX_IAM_TOKEN", ""),
        ocr_lang=os.getenv("OCR_LANG", "rus+eng"),
        max_upload_size_mb=int(os.getenv("MAX_UPLOAD_SIZE_MB", "50")),
        temp_dir=Path(os.getenv("TEMP_DIR", "./temp")),
        mask_style=os.getenv("MASK_STYLE", "asterisks"),
        chunk_size=int(os.getenv("CHUNK_SIZE", "6000")),
    )
