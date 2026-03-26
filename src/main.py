import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers.auth_router import auth_router
from routers.user_router import user_router
from utils.logging import logger
from core.config import settings

app = FastAPI(
    title="User Service API",
    description="Service for working with users",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,  # TODO указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(user_router)

if __name__ == "__main__":
    logger.info("Starting User Service on 0.0.0.0:8002")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8002,
        reload=False,  # Для продакшена лучше False
        log_level="info"
    )