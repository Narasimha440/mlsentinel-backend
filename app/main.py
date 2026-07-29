"""
Main file for mlsentinal backedn of fastapi
"""
from app.routes.report import router as report_router
from app.routes.history import router as history_router
from app.routes.projects import router as projects_router
from app.routes.dashboard import router as dashboard_router
from app.routes.api_keys import router as api_keys_router
from app.routes.onboarding import router as onboarding_router
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title = "MLSentinal API",
    description = "Backend api for mlsentinal to sending the model details to the official mlsentinal dashboard",
    version = "0.1.4"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://api.mlsentinel.dev/",
        "https://api.mlsentinel.dev//api/onboarding/status"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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

app.include_router(
    projects_router,
    prefix="/api",
    tags=["Projects"]
)

app.include_router(
    dashboard_router,
    prefix="/api",
    tags=["Dashboard"]
)

app.include_router(
    api_keys_router,
    prefix="/api",
    tags=["API Keys"]
)

app.include_router(
    onboarding_router,
    prefix="/api",
    tags=["Onboarding"]
)

@app.get("/")
def root():
    return {
        "message": "Welcome to mlsentinal api endpoint",
        "status": "running"
    }