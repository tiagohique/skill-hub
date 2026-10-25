import os
from collections.abc import AsyncIterator

import httpx
import pytest_asyncio

from hub.config import Settings
from hub.main import create_app
from tests.helpers import running

SKILL = "---\nname: my-skill\ndescription: Faz algo útil\n---\n# Corpo\n"


def skill_md(version_extra: str = "") -> bytes:
    return (SKILL + version_extra).encode()


@pytest_asyncio.fixture
async def anon(clean_db: None) -> AsyncIterator[httpx.AsyncClient]:
    """Cliente sem login."""
    settings = Settings(
        database_url=os.environ["TEST_DATABASE_URL"],
        migration_database_url=os.environ["TEST_MIGRATION_DATABASE_URL"],
        blob_backend="postgres",
        max_file_bytes=2000,
        max_bundle_bytes=5000,
        max_files=10,
    )
    app = create_app(settings)
    async with running(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
            yield c


@pytest_asyncio.fixture
async def client(anon: httpx.AsyncClient) -> httpx.AsyncClient:
    """Cliente já autenticado como admin (o cookie fica na sessão do cliente)."""
    r = await anon.post("/api/auth/login", json={"username": "admin", "password": "admin"})
    assert r.status_code == 200, r.text
    return anon


async def upload(
    client: httpx.AsyncClient,
    data: bytes | None = None,
    version: str = "1.0.0",
    filename: str = "SKILL.md",
) -> httpx.Response:
    return await client.post(
        "/api/skills/upload",
        files={"file": (filename, data if data is not None else skill_md())},
        data={"version": version},
    )


async def promote(client: httpx.AsyncClient, to: str, version: str = "1.0.0") -> httpx.Response:
    return await client.post(f"/api/skills/my-skill/versions/{version}/promote", json={"to": to})


def assert_error(response: httpx.Response, status: int, code: str) -> None:
    assert response.status_code == status, response.text
    body = response.json()
    assert set(body) == {"code", "message"}
    assert body["code"] == code
    assert body["message"]


async def test_health(client: httpx.AsyncClient) -> None:
    assert (await client.get("/api/health")).json() == {"status": "ok"}


async def test_upload_md_returns_201_draft(client: httpx.AsyncClient) -> None:
    r = await upload(client)
    assert r.status_code == 201, r.text
    body = r.json()
    assert (body["name"], body["version"], body["status"]) == ("my-skill", "1.0.0", "draft")
    assert body["files"][0]["path"] == "SKILL.md"
    assert len(body["files"][0]["sha256"]) == 64
    assert body["created_by"] == "admin"


async def test_repeated_version_is_409(client: httpx.AsyncClient) -> None:
    assert (await upload(client)).status_code == 201
    assert_error(await upload(client, skill_md("outro\n")), 409, "version_exists")


async def test_zip_with_path_traversal_is_422(client: httpx.AsyncClient) -> None:
    import io
    import zipfile

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("SKILL.md", SKILL)
        zf.writestr("../evil.md", "x")
    assert_error(await upload(client, buf.getvalue(), filename="s.zip"), 422, "invalid_skill")


async def test_invalid_semver_is_422(client: httpx.AsyncClient) -> None:
    assert_error(await upload(client, version="1.0"), 422, "invalid_skill")


async def test_oversized_upload_is_413(client: httpx.AsyncClient) -> None:
    assert_error(await upload(client, b"x" * 6000), 413, "limit_exceeded")
    assert_error(await upload(client, skill_md("y" * 2500)), 413, "limit_exceeded")


async def test_missing_form_fields_is_422_invalid_request(client: httpx.AsyncClient) -> None:
    r = await client.post("/api/skills/upload", data={"version": "1.0.0"})
    assert_error(r, 422, "invalid_request")


async def test_list_skills_shows_channels(client: httpx.AsyncClient) -> None:
    await upload(client)
    [item] = (await client.get("/api/skills")).json()
    assert item == {
        "name": "my-skill",
        "domain": "geral",
        "owner": "admin",
        "stable": None,
        "beta": None,
        "status": "draft",
    }
    await promote(client, "beta")
    await promote(client, "stable")
    [item] = (await client.get("/api/skills")).json()
    assert (item["stable"], item["beta"]) == ("1.0.0", "1.0.0")


async def test_skill_detail(client: httpx.AsyncClient) -> None:
    await upload(client)
    await upload(client, skill_md("v2\n"), version="1.1.0")
    body = (await client.get("/api/skills/my-skill")).json()
    assert body["name"] == "my-skill"
    assert body["description"] == "Faz algo útil"
    assert {v["version"] for v in body["versions"]} == {"1.0.0", "1.1.0"}
    assert body["channels"] == {}
    assert body["versions"][0]["created_at"].startswith("20")  # ISO 8601


async def test_version_detail_has_files_and_hashes(client: httpx.AsyncClient) -> None:
    await upload(client)
    body = (await client.get("/api/skills/my-skill/versions/1.0.0")).json()
    assert body["bundle_sha256"]
    assert body["files"][0]["size"] == len(skill_md())
    assert body["frontmatter"]["name"] == "my-skill"


async def test_promote_flow_and_invalid_transition(client: httpx.AsyncClient) -> None:
    await upload(client)
    assert_error(await promote(client, "stable"), 409, "invalid_transition")
    r = await promote(client, "beta")
    assert r.status_code == 200 and r.json()["status"] == "beta"
    r = await promote(client, "stable")
    assert r.json()["status"] == "stable"


async def test_promote_to_retired_is_422_invalid_request(client: httpx.AsyncClient) -> None:
    await upload(client)
    assert_error(await promote(client, "retired"), 422, "invalid_request")


async def test_deprecate(client: httpx.AsyncClient) -> None:
    await upload(client)
    await promote(client, "beta")
    r = await client.post("/api/skills/my-skill/versions/1.0.0/deprecate")
    assert r.status_code == 200 and r.json()["status"] == "deprecated"
    assert_error(
        await client.post("/api/skills/my-skill/versions/1.0.0/deprecate"),
        409,
        "invalid_transition",
    )


async def test_not_found(client: httpx.AsyncClient) -> None:
    assert_error(await client.get("/api/skills/nope"), 404, "not_found")
    assert_error(await client.get("/api/skills/nope/versions/1.0.0"), 404, "not_found")
    assert_error(
        await client.post("/api/skills/nope/versions/1.0.0/promote", json={"to": "beta"}),
        404,
        "not_found",
    )
    assert_error(await client.get("/api/rota-inexistente"), 404, "not_found")
