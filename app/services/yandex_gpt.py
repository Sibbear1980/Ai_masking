import json
import logging
import re
from typing import List, Tuple, Dict, Any

import httpx

from app.config import Settings
from app.models.entity_model import SensitiveEntity

logger = logging.getLogger(__name__)

PROMPT_TEMPLATE = (
    "Найди персональные данные, названия компаний, проекты и реквизиты в тексте. "
    "Верни JSON с ключом entities, где каждый объект содержит поля type, text, start, end. "
    "Формат примера: {{\"entities\": [{{\"type\": \"PERSON\", \"text\": \"Иванов Иван\", \"start\": 0, \"end\": 12}}]}}. "
    "Текст:\n{payload}"
)


class YandexGPTClient:
    def __init__(self, settings: Settings):
        self.api_key = settings.yandex_gpt_api_key
        self.api_url = settings.yandex_gpt_api_url
        self.model_uri = settings.yandex_gpt_model_uri
        self.folder_id = settings.yandex_folder_id
        self.iam_token = settings.yandex_iam_token
        self.chunk_size = settings.chunk_size
        self._headers = self._build_headers()

    async def detect_sensitive_data(self, text: str) -> Tuple[List[SensitiveEntity], List[Dict[str, Any]]]:
        if not text.strip():
            return [], []

        if not self.api_key and not self.iam_token:
            logger.warning("YANDEX_GPT_API_KEY or YANDEX_IAM_TOKEN is not set. Returning empty entity list.")
            return [], []

        entities: List[SensitiveEntity] = []
        logs: List[Dict[str, Any]] = []
        async with httpx.AsyncClient(timeout=60) as client:
            for chunk_text, offset in _chunk_text(text, self.chunk_size):
                request_body = self._build_request_body(chunk_text)
                logs.append(
                    {
                        "direction": "request",
                        "offset": offset,
                        "length": len(chunk_text),
                        "body": request_body,
                    }
                )
                try:
                    response = await client.post(self.api_url, headers=self._headers, json=request_body)
                    if response.status_code == 401:
                        body = response.text[:2000]
                        logger.error("Unauthorized: check API key/IAM token. Body: %s", body)
                        logs.append(
                            {
                                "direction": "error",
                                "offset": offset,
                                "status": response.status_code,
                                "error": "401 Unauthorized. Проверьте ключ/токен/права.",
                                "body": body,
                            }
                        )
                        continue

                    response.raise_for_status()
                    logs.append(
                        {
                            "direction": "response",
                            "offset": offset,
                            "status": response.status_code,
                            "body": response.text[:2000],
                        }
                    )
                    entities.extend(self._parse_entities(response, offset))
                except Exception as exc:  # noqa: BLE001
                    error_message = str(exc)
                    body = ""
                    if isinstance(exc, httpx.HTTPStatusError) and exc.response is not None:
                        body = exc.response.text[:2000]
                    logger.error("Yandex GPT request failed: %s %s", error_message, body)
                    logs.append(
                        {
                            "direction": "error",
                            "offset": offset,
                            "error": error_message,
                            "body": body,
                        }
                    )
                    continue

        return entities, logs

    def _parse_entities(self, response: httpx.Response, offset: int) -> List[SensitiveEntity]:
        data = response.json()
        text_payload = (
            data.get("result", {})
            .get("alternatives", [{}])[0]
            .get("message", {})
            .get("text")
        )
        entities_field = data.get("entities")

        payload = entities_field or text_payload
        if not payload:
            return []

        parsed = _safe_json_load(payload)
        if not parsed:
            return []

        entities = []
        for item in parsed.get("entities", []):
            try:
                entities.append(
                    SensitiveEntity(
                        type=item.get("type", "UNKNOWN"),
                        text=item.get("text", ""),
                        start=int(item.get("start", 0)) + offset,
                        end=int(item.get("end", 0)) + offset,
                    )
                )
            except Exception:
                continue
        return entities

    def _build_request_body(self, chunk: str) -> dict:
        model_uri = self.model_uri or (f"gpt://{self.folder_id}/yandexgpt" if self.folder_id else "")
        return {
            "modelUri": model_uri,
            "completionOptions": {"stream": False, "temperature": 0.1, "maxTokens": 1000},
            "messages": [
                {"role": "system", "text": "Ты извлекаешь сущности из текста."},
                {"role": "user", "text": PROMPT_TEMPLATE.format(payload=chunk)},
            ],
        }

    def _build_headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Api-Key {self.api_key}"
        elif self.iam_token:
            headers["Authorization"] = f"Bearer {self.iam_token}"
            if self.folder_id:
                headers["x-folder-id"] = self.folder_id
        return headers


def _chunk_text(text: str, chunk_size: int):
    start = 0
    length = len(text)
    while start < length:
        end = min(start + chunk_size, length)
        yield text[start:end], start
        start = end


def _safe_json_load(payload: Any) -> Dict[str, Any]:
    if isinstance(payload, dict):
        return payload

    if not isinstance(payload, str):
        logger.error("Failed to decode Yandex GPT response: %s", payload)
        return {}

    cleaned = payload.strip("` \n")
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"{.*}", cleaned, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass

    logger.error("Failed to decode Yandex GPT response: %s", payload)
    return {}
