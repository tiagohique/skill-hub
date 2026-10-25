from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from hub.api.errors import install_error_handlers
from hub.api.routes import router
from hub.config import Settings
from hub.service.skill_service import SkillService
from hub.service.validation import UploadLimits
from hub.store.factory import make_blob_store


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        engine = create_async_engine(settings.database_url)
        sessions = async_sessionmaker(engine, expire_on_commit=False)
        app.state.service = SkillService(
            sessions,
            make_blob_store(settings, sessions),
            UploadLimits(settings.max_file_bytes, settings.max_bundle_bytes, settings.max_files),
        )
        yield
        await engine.dispose()

    app = FastAPI(title="Skills Hub", lifespan=lifespan)
    app.state.settings = settings
    install_error_handlers(app)
    app.include_router(router)
    return app
