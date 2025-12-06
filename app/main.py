import logging

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.dependencies import settings, storage
from app.routers import download, preview, upload

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

app = FastAPI(title="Web-сервис маскирования ПД")

app.include_router(upload.router)
app.include_router(preview.router)
app.include_router(download.router)

app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.on_event("startup")
async def startup_cleanup():
    storage.cleanup()
