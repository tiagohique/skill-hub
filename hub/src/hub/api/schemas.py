from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict


class _Out(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class FileOut(_Out):
    path: str
    sha256: str
    size: int


class SkillSummaryOut(_Out):
    name: str
    domain: str
    owner: str
    stable: str | None
    beta: str | None
    status: str


class VersionSummaryOut(_Out):
    version: str
    status: str
    bundle_sha256: str
    created_by: str
    created_at: datetime


class SkillDetailOut(_Out):
    name: str
    domain: str
    owner: str
    description: str
    channels: dict[str, str]
    versions: list[VersionSummaryOut]


class VersionDetailOut(_Out):
    name: str
    version: str
    status: str
    frontmatter: dict[str, Any]
    bundle_sha256: str
    created_by: str
    created_at: datetime
    files: list[FileOut]


class PromoteIn(BaseModel):
    to: Literal["beta", "stable"]


class LoginIn(BaseModel):
    username: str
    password: str


class ThemeIn(BaseModel):
    theme: str


class UserOut(_Out):
    username: str
    theme: str
