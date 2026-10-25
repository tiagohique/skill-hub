from itertools import product

import pytest

from hub.domain.errors import HubError, InvalidTransitionError
from hub.domain.models import Channel, Status, channel_for, check_transition

ALLOWED = [
    (Status.DRAFT, Status.BETA),
    (Status.BETA, Status.STABLE),
    (Status.BETA, Status.DEPRECATED),
    (Status.STABLE, Status.DEPRECATED),
    (Status.DEPRECATED, Status.RETIRED),
]
FORBIDDEN = [pair for pair in product(Status, Status) if pair not in ALLOWED]


@pytest.mark.parametrize(("current", "target"), ALLOWED)
def test_allowed_transitions_pass(current: Status, target: Status) -> None:
    check_transition(current, target)


@pytest.mark.parametrize(("current", "target"), FORBIDDEN)
def test_forbidden_transitions_raise(current: Status, target: Status) -> None:
    with pytest.raises(InvalidTransitionError) as exc:
        check_transition(current, target)
    assert exc.value.code == "invalid_transition"
    assert f"{current}" in str(exc.value)


def test_channel_for() -> None:
    assert channel_for(Status.BETA) is Channel.BETA
    assert channel_for(Status.STABLE) is Channel.STABLE
    assert channel_for(Status.DRAFT) is None
    assert channel_for(Status.DEPRECATED) is None
    assert channel_for(Status.RETIRED) is None


def test_error_codes() -> None:
    from hub.domain import errors

    expected = {
        "SkillValidationError": "invalid_skill",
        "LimitExceededError": "limit_exceeded",
        "VersionConflictError": "version_exists",
        "InvalidTransitionError": "invalid_transition",
        "NotFoundError": "not_found",
        "IntegrityError": "integrity_error",
    }
    for name, code in expected.items():
        cls = getattr(errors, name)
        assert issubclass(cls, HubError)
        assert cls("msg").code == code
