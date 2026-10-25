from collections.abc import AsyncIterator
from contextlib import AsyncExitStack, asynccontextmanager

from fastapi import FastAPI
from mcp.server.streamable_http_manager import StreamableHTTPASGIApp
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from starlette.routing import Route

from hub.api.errors import install_error_handlers
from hub.api.routes import router
from hub.config import Settings
from hub.mcp.server import build_mcp_server, build_session_manager
from hub.service.skill_service import SkillService
from hub.service.validation import UploadLimits
from hub.store.factory import make_blob_store


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()

    # O servidor MCP vive no mesmo app ASGI, em /mcp; o SkillService só existe depois do lifespan.
    mcp_server = build_mcp_server(lambda: app.state.service)
    mcp_manager = build_session_manager(mcp_server)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        engine = create_async_engine(settings.database_url)
        sessions = async_sessionmaker(engine, expire_on_commit=False)
        app.state.service = SkillService(
            sessions,
            make_blob_store(settings, sessions),
            UploadLimits(settings.max_file_bytes, settings.max_bundle_bytes, settings.max_files),
        )
        async with AsyncExitStack() as stack:
            await stack.enter_async_context(mcp_manager.run())
            yield
        await engine.dispose()

    app = FastAPI(title="Skills Hub", lifespan=lifespan)
    app.state.settings = settings
    install_error_handlers(app)
    app.include_router(router)
    app.router.routes.append(Route("/mcp", endpoint=StreamableHTTPASGIApp(mcp_manager)))
    return app
