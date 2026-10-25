"""Publica as skills de exemplo no hub: upload 1.0.0, promoção a beta e a stable.

Uso (dentro do Compose): docker compose run --rm hub-test python /scripts/demo.py [url_da_api]
"""

import io
import sys
import zipfile
from pathlib import Path

import httpx

VERSION = "1.0.0"
EXAMPLES = Path("/examples/skills")


def zip_skill(folder: Path) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(p for p in folder.rglob("*") if p.is_file()):
            zf.write(path, path.relative_to(folder).as_posix())
    return buf.getvalue()


def main(api: str) -> int:
    with httpx.Client(base_url=api, timeout=30) as client:
        # A API exige login; na POC o usuário inicial é admin/admin.
        r = client.post("/auth/login", json={"username": "admin", "password": "admin"})
        if r.status_code != 200:
            print(f"[erro] login: {r.status_code} {r.text}")
            return 1
        for folder in sorted(p for p in EXAMPLES.iterdir() if p.is_dir()):
            name = folder.name
            r = client.post(
                "/skills/upload",
                files={"file": (f"{name}.zip", zip_skill(folder))},
                data={"version": VERSION},
            )
            if r.status_code == 201:
                print(f"[ok] {name}@{VERSION} enviada como draft")
            elif r.status_code == 409:
                print(f"[aviso] {name}@{VERSION} já existe; seguindo para a promoção")
            else:
                print(f"[erro] upload de {name}: {r.status_code} {r.text}")
                return 1
            for target in ("beta", "stable"):
                r = client.post(
                    f"/skills/{name}/versions/{VERSION}/promote", json={"to": target}
                )
                if r.status_code == 200:
                    print(f"[ok] {name}@{VERSION} promovida para {target}")
                elif r.status_code == 409:
                    print(f"[aviso] {name}@{VERSION}: {r.json()['message']}")
                else:
                    print(f"[erro] promoção de {name}: {r.status_code} {r.text}")
                    return 1
        for skill in client.get("/skills").json():
            print(f"  {skill['name']}: stable={skill['stable']} beta={skill['beta']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "http://hub:8000/api"))
