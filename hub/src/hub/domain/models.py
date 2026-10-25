from dataclasses import dataclass
from enum import StrEnum

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
