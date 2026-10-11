from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from app.api.router.job import router as job_router
from app.api.router.certificate import router as certificate_router
app = FastAPI(
    title="Bulk Certificate Generator",
    version="1.0.0"
)

APP_DIR= Path(__file__).resolve().parent

app.include_router(job_router)
app.include_router(certificate_router)

app.mount("/static", StaticFiles(directory=APP_DIR/"static"), name="static")
@app.get("/", include_in_schema=False)
def homepage():
    return FileResponse(APP_DIR/"static"/"index.html")