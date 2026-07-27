"""
Main file for mlsentinal backedn of fastapi
"""
from app.routes.report import router as report_router
from app.routes.history import router as history_router
from fastapi import FastAPI

app = FastAPI(
    title = "MLSentinal API",
    description = "Backend api for mlsentinal to sending the model details to the official mlsentinal dashboard",
    version = "0.1.4"
)

app.include_router(
    report_router,
    prefix="/api",
    tags=["Reports"]
)

app.include_router(
    history_router,
    prefix="/api",
    tags=["History"]
)

@app.get("/")
def root():
    return {
        "message": "Welcome to mlsentinal api endpoint",
        "status": "running"
    }