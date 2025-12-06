from app.config import Settings, load_settings
from app.services.file_storage import FileStorageService
from app.services.yandex_gpt import YandexGPTClient

settings = load_settings()
storage = FileStorageService(settings.temp_dir)
gpt_client = YandexGPTClient(settings)


def get_settings() -> Settings:
    return settings


def get_storage() -> FileStorageService:
    return storage


def get_gpt_client() -> YandexGPTClient:
    return gpt_client
