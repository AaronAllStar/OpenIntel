from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.app.api.routes import health, investigations
from src.app.infrastructure.config import get_settings
from src.app.infrastructure.database import Base, engine
from src.app.infrastructure.logging import logger, setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    setup_logging()
    logger.info("Initializing OpenIntel database tables...")
    import src.app.infrastructure.models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    logger.info("OpenIntel started successfully")
    yield
    logger.info("OpenIntel shutting down...")


settings = get_settings()

app = FastAPI(
    title="OpenIntel API",
    description="OSINT investigation platform API",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS configuration for local React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(investigations.router, prefix="/api/v1")
app.include_router(health.router, prefix="/api/v1")

# Mount built frontend if available
ui_dist_path = Path("src/ui/dist")
if ui_dist_path.exists():
    from fastapi.staticfiles import StaticFiles

    app.mount("/", StaticFiles(directory=str(ui_dist_path), html=True), name="ui")
else:
    @app.get("/")
    def root() -> dict:
        return {
            "app": "OpenIntel",
            "version": "0.1.0",
            "status": "online",
            "docs": "/docs",
        }
