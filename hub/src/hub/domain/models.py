from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any

from hub.domain.errors import InvalidTransitionError


class Status(StrEnum):
    DRAFT = "draft"
    BETA = "beta"
    STABLE = "stable"
    DEPRECATED = "deprecated"
    RETIRED = "retired"


class Channel(StrEnum):
    BETA = "beta"
    STABLE = "stable"


ALLOWED_TRANSITIONS: frozenset[tuple[Status, Status]] = frozenset(
    {
        (Status.DRAFT, Status.BETA),
        (Status.BETA, Status.STABLE),
        (Status.BETA, Status.DEPRECATED),
        (Status.STABLE, Status.DEPRECATED),
        (Status.DEPRECATED, Status.RETIRED),
    }
)


def check_transition(current: Status, target: Status) -> None:
    if (current, target) not in ALLOWED_TRANSITIONS:
        raise InvalidTransitionError(f"Transição de {current} para {target} não é permitida.")


def channel_for(status: Status) -> Channel | None:
    match status:
        case Status.BETA:
            return Channel.BETA
        case Status.STABLE:
            return Channel.STABLE
        case _:
            return None


@dataclass(frozen=True)
class SkillFile:
    path: str
    data: bytes


@dataclass(frozen=True)
class FileEntry:
    path: str
    sha256: str
    size: int


@dataclass(frozen=True)
class SkillSummary:
    name: str
    domain: str
    owner: str
    stable: str | None
    beta: str | None


@dataclass(frozen=True)
class VersionSummary:
    version: str
    status: Status
    bundle_sha256: str
    created_by: str
    created_at: datetime


@dataclass(frozen=True)
class SkillDetail:
    name: str
    domain: str
    owner: str
    description: str
    channels: dict[Channel, str]
    versions: list[VersionSummary]


@dataclass(frozen=True)
class VersionDetail:
    name: str
    version: str
    status: Status
    frontmatter: dict[str, Any]
    bundle_sha256: str
    created_by: str
    created_at: datetime
    files: list[FileEntry]


@dataclass(frozen=True)
class PublishedSkill:
    name: str
    description: str
    version: str
    bundle_sha256: str
    files: list[FileEntry]
