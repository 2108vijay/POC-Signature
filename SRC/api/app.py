from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from SRC.api.routers import auth, health, upload, files, detect
from SRC.middleware.request_logger import log_requests
from SRC.utils.logger import logger

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Signature Verification API",
        description="Document classification + signature detection + MinIO storage",
        version="2.0.0",
    )

    logger.info("Application starting...")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.middleware("http")(log_requests)

   
    app.include_router(auth.router)
    app.include_router(health.router)
    app.include_router(upload.router)
    app.include_router(files.router)

    # Protected routes
    app.include_router(detect.router)

    return app