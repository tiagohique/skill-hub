import pytest

from hub.domain.semver import is_semver


@pytest.mark.parametrize(
    "value", ["1.0.0", "0.1.0-beta.1", "1.2.3+build.5", "10.20.30", "1.0.0-rc.1+x"]
)
def test_valid(value: str) -> None:
    assert is_semver(value)


@pytest.mark.parametrize("value", ["1.0", "01.0.0", "v1.0.0", "1.0.0.0", "", "1.0.0-", "a.b.c"])
def test_invalid(value: str) -> None:
    assert not is_semver(value)
