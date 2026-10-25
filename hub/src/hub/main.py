from fastapi import APIRouter, FastAPI

from hub.config import Settings


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    app = FastAPI(title="Skills Hub")
    app.state.settings = settings

    api = APIRouter(prefix="/api")

    @api.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(api)
    return app
