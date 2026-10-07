from fastapi import FastAPI

from app.api.auth import router as auth_router
from app.api.devices import router as device_router
from app.api.employees import router as employee_router
from app.core.config import settings
from app.db.session import create_db_and_tables
from app.api.events import router as events_router
from app.api.behavior import router as behavior_router
from app.api.detection import router as detection_router
from app.api.ml import router as ml_router
from app.api.alerts import router as alerts_router
from app.api.exceptions import router as exceptions_router
from app.api.policies import router as policies_router
from fastapi.middleware.cors import CORSMiddleware
from app.api.websocket import router as websocket_router

app = FastAPI(
    title=settings.APP_NAME,
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    create_db_and_tables()


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": settings.APP_NAME
    }


app.include_router(auth_router)
app.include_router(employee_router)
app.include_router(device_router)
app.include_router(events_router)
app.include_router(behavior_router)
app.include_router(detection_router)
app.include_router(ml_router)
app.include_router(alerts_router)
app.include_router(exceptions_router)
app.include_router(policies_router)
app.include_router(websocket_router)