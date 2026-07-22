"""
Main file for mlsentinal backedn of fastapi
"""
from app.routes.report import router as report_router
from fastapi import FastAPI

app = FastAPI(
    title = "MLSentinal API",
    description = "Backend api for mlsentinal to sending the model details to the official mlsentinal dashboard",
    version = "0.1.0"
)

app.include_router(
    report_router,
    prefix="/api",
    tags=["Reports"]
)

@app.get("/")
def root():
    return {
        "message": "Welcome to mlsentinal api endpoint",
        "status": "running"
    }