"""Lê as skills stable pelo MCP e confere cada hash.

Para cada arquivo: SHA-256 e tamanho recalculados batem com o digest da listagem, e o
hash do pacote recalculado bate com o `bundle_sha256` da API REST. Sai com código 1 se
algo divergir ou falhar (por exemplo, erro de integridade do hub).

Uso: docker compose run --rm hub-test python /scripts/verify_mcp.py [url_do_mcp]
"""

import asyncio
import base64
import hashlib
import sys
from typing import Any

import httpx
import mcp_types as types
from mcp import Client
from mcp.shared.exceptions import MCPError
from pydantic import BaseModel

from hub.domain.hashing import bundle_sha256
from hub.domain.models import FileEntry


class AnyResult(BaseModel, extra="allow"):
    pass


async def verify(url: str) -> int:
    api = url.removesuffix("/mcp") + "/api"
    failures = 0
    # A API REST exige login (o MCP não); na POC o usuário inicial é admin/admin.
    rest = httpx.Client(base_url=api, timeout=30)
    rest.post("/auth/login", json={"username": "admin", "password": "admin"}).raise_for_status()
    async with Client(url, client_info=types.Implementation(name="verify-mcp", version="1.0")) as client:
        result = await client.session.send_request(
            types.Request(method="skills/list", params=types.PaginatedRequestParams()), AnyResult
        )
        skills: list[dict[str, Any]] = result.model_dump()["skills"]
        if not skills:
            print("[falha] nenhuma skill stable publicada")
            return 1
        for skill in skills:
            name = skill["frontmatter"]["name"]
            entries: list[FileEntry] = []
            for res in skill["resources"]:
                path = res["uri"].removeprefix(f"skill://{name}/")
                try:
                    read = await client.read_resource(res["uri"])
                except MCPError as exc:
                    print(f"[falha] {name}/{path}: {exc}")
                    failures += 1
                    continue
                content = read.contents[0]
                data = (
                    content.text.encode()
                    if isinstance(content, types.TextResourceContents)
                    else base64.b64decode(content.blob)
                )
                sha = hashlib.sha256(data).hexdigest()
                ok = f"sha256:{sha}" == res["digest"] and len(data) == res["size"]
                entries.append(FileEntry(path, sha, len(data)))
                print(f"[{'ok' if ok else 'falha'}] {name}/{path} {res['digest'][:19]}…")
                failures += 0 if ok else 1
            detail = rest.get(f"/skills/{name}").json()
            version = detail["channels"]["stable"]
            expected = rest.get(f"/skills/{name}/versions/{version}").json()["bundle_sha256"]
            bundle_ok = bundle_sha256(entries) == expected
            print(f"[{'ok' if bundle_ok else 'falha'}] {name}@{version} hash do pacote")
            failures += 0 if bundle_ok else 1
    print("Tudo conferido." if failures == 0 else f"{failures} divergência(s).")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(verify(sys.argv[1] if len(sys.argv) > 1 else "http://hub:8000/mcp")))
