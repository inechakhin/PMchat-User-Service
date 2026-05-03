import uvicorn
from fastapi import FastAPI

from routers.auth_router import auth_router
from routers.user_router import user_router
from utils.logging import logger

app = FastAPI(
    title="User Service API",
    description="Service for working with users",
    version="1.0.0",
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