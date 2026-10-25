import httpx
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from tests.integration.test_api import anon, assert_error, client, skill_md, upload  # noqa: F401

PROTECTED = [
    ("GET", "/api/skills"),
    ("GET", "/api/skills/x"),
    ("GET", "/api/skills/x/versions/1.0.0"),
    ("POST", "/api/skills/x/versions/1.0.0/promote"),
    ("POST", "/api/skills/x/versions/1.0.0/deprecate"),
    ("POST", "/api/skills/upload"),
    ("GET", "/api/auth/me"),
]


@pytest.mark.parametrize(("method", "path"), PROTECTED)
async def test_protected_routes_need_login(anon: httpx.AsyncClient, method: str, path: str) -> None:  # noqa: F811
    assert_error(await anon.request(method, path), 401, "unauthorized")


async def test_health_stays_open(anon: httpx.AsyncClient) -> None:  # noqa: F811
    assert (await anon.get("/api/health")).status_code == 200


async def test_login_sets_http_only_cookie_and_me_works(anon: httpx.AsyncClient) -> None:  # noqa: F811
    r = await anon.post("/api/auth/login", json={"username": "admin", "password": "admin"})
    assert r.json() == {"username": "admin", "theme": "dark"}
    cookie = r.headers["set-cookie"].lower()
    assert "httponly" in cookie and "samesite=lax" in cookie
    assert (await anon.get("/api/auth/me")).json()["username"] == "admin"


async def test_wrong_password_is_401(anon: httpx.AsyncClient) -> None:  # noqa: F811
    r = await anon.post("/api/auth/login", json={"username": "admin", "password": "x"})
    assert_error(r, 401, "unauthorized")
    assert "set-cookie" not in r.headers


async def test_logout_ends_session(client: httpx.AsyncClient) -> None:  # noqa: F811
    assert (await client.post("/api/auth/logout")).status_code == 204
    assert_error(await client.get("/api/skills"), 401, "unauthorized")


async def test_theme_roundtrip_and_validation(client: httpx.AsyncClient) -> None:  # noqa: F811
    r = await client.put("/api/auth/theme", json={"theme": "light"})
    assert r.json()["theme"] == "light"
    assert (await client.get("/api/auth/me")).json()["theme"] == "light"
    assert_error(
        await client.put("/api/auth/theme", json={"theme": "roxo"}), 422, "invalid_request"
    )


async def test_audit_actor_is_logged_in_user(
    client: httpx.AsyncClient,  # noqa: F811
    owner_engine: AsyncEngine,
) -> None:
    await upload(client)
    async with owner_engine.connect() as conn:
        actor = (await conn.execute(text("SELECT actor FROM audit_events"))).scalar_one()
        by = (await conn.execute(text("SELECT created_by FROM skill_versions"))).scalar_one()
    assert (actor, by) == ("admin", "admin")


async def test_list_has_overall_status(client: httpx.AsyncClient) -> None:  # noqa: F811
    await upload(client)
    assert (await client.get("/api/skills")).json()[0]["status"] == "draft"
    await client.post("/api/skills/my-skill/versions/1.0.0/promote", json={"to": "beta"})
    assert (await client.get("/api/skills")).json()[0]["status"] == "beta"
    await client.post("/api/skills/my-skill/versions/1.0.0/promote", json={"to": "stable"})
    assert (await client.get("/api/skills")).json()[0]["status"] == "stable"
    await client.post("/api/skills/my-skill/versions/1.0.0/deprecate")
    assert (await client.get("/api/skills")).json()[0]["status"] == "deprecated"


async def test_mcp_stays_open_without_login(anon: httpx.AsyncClient) -> None:  # noqa: F811
    r = await anon.post(
        "/mcp",
        json={"jsonrpc": "2.0", "id": 1, "method": "ping"},
        headers={"Accept": "application/json, text/event-stream"},
    )
    assert r.status_code != 401
