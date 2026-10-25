"""Ponto a ponto: upload das skills de exemplo, promoção, leitura pelo MCP e hashes."""

import hashlib
import io
import zipfile
from pathlib import Path

import mcp_types as types
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from hub.domain.hashing import bundle_sha256
from hub.domain.models import FileEntry, Status
from hub.mcp.server import SkillsListParams
from tests.mcp_support import Hub, call

EXAMPLES = Path("/examples/skills")


def zip_folder(folder: Path) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for path in sorted(p for p in folder.rglob("*") if p.is_file()):
            zf.write(path, path.relative_to(folder).as_posix())
    return buf.getvalue()


def example_folders() -> list[Path]:
    return sorted(p for p in EXAMPLES.iterdir() if p.is_dir())


def original_bytes(skill: str, path: str) -> bytes:
    return (EXAMPLES / skill / path).read_bytes()


async def test_example_skills_published_and_consumed(hub: Hub, app_engine: AsyncEngine) -> None:
    folders = example_folders()
    assert {f.name for f in folders} == {"html-landing-page", "fastapi-endpoint"}

    for folder in folders:
        await hub.service.upload(
            filename=f"{folder.name}.zip", data=zip_folder(folder), version="1.0.0", actor="portal"
        )
        await hub.service.promote(folder.name, "1.0.0", Status.BETA, "portal")
        await hub.service.promote(folder.name, "1.0.0", Status.STABLE, "portal")

    read_count = 0
    async with hub.client() as client:
        listing = await call(client, "skills/list", SkillsListParams())
        assert {s["frontmatter"]["name"] for s in listing["skills"]} == {f.name for f in folders}
        for skill in listing["skills"]:
            name = skill["frontmatter"]["name"]
            entries = []
            for res in skill["resources"]:
                path = res["uri"].removeprefix(f"skill://{name}/")
                result = await client.read_resource(res["uri"])
                [content] = result.contents
                assert isinstance(content, types.TextResourceContents)
                data = content.text.encode()
                original = original_bytes(name, path)
                assert data == original
                assert res["digest"] == f"sha256:{hashlib.sha256(data).hexdigest()}"
                assert res["size"] == len(data)
                entries.append(FileEntry(path, hashlib.sha256(data).hexdigest(), len(data)))
                read_count += 1
            stored = await hub.service.get_version(name, "1.0.0")
            assert bundle_sha256(entries) == stored.bundle_sha256

    async with app_engine.connect() as conn:
        rows = (
            await conn.execute(
                text("SELECT action, count(*) AS n FROM audit_events GROUP BY action")
            )
        ).all()
    counts = {r.action: r.n for r in rows}
    assert counts["upload"] == 2
    assert counts["promote"] == 4
    assert counts["mcp_read"] == read_count
