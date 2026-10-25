import httpx

from hub.config import Settings
from hub.main import create_app


async def test_health_returns_ok() -> None:
    settings = Settings(
        database_url="x",
        migration_database_url="y",
        blob_backend="postgres",
        max_file_bytes=1,
        max_bundle_bytes=1,
        max_files=1,
    )
    app = create_app(settings)
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
