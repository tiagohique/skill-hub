import httpx
import pytest

from tests.integration.test_api import anon  # noqa: F401

OK = ("admin", "B3123")


@pytest.mark.parametrize("path", ["/docs", "/openapi.json", "/mcp-docs"])
async def test_docs_need_password(anon: httpx.AsyncClient, path: str) -> None:  # noqa: F811
    r = await anon.get(path)
    assert r.status_code == 401
    assert r.headers["www-authenticate"].startswith("Basic")
    assert (await anon.get(path, auth=("admin", "errada"))).status_code == 401


async def test_swagger_and_openapi_with_password(anon: httpx.AsyncClient) -> None:  # noqa: F811
    page = await anon.get("/docs", auth=OK)
    assert page.status_code == 200 and "swagger" in page.text.lower()
    spec = (await anon.get("/openapi.json", auth=OK)).json()
    assert "/api/skills" in spec["paths"] and "/api/auth/login" in spec["paths"]
    assert "/docs" not in spec["paths"]  # a documentação não aparece nela mesma


async def test_mcp_docs_lists_tools_and_methods(anon: httpx.AsyncClient) -> None:  # noqa: F811
    r = await anon.get("/mcp-docs", auth=OK)
    assert r.status_code == 200
    for text in ("list_skills", "get_skill", "skills/list", "skills/get", "/mcp"):
        assert text in r.text


async def test_docs_do_not_open_the_api(anon: httpx.AsyncClient) -> None:  # noqa: F811
    assert (await anon.get("/api/skills", auth=OK)).status_code == 401
