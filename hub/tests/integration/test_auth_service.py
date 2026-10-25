import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from hub.domain.errors import UnauthorizedError
from hub.service.auth_service import AuthService, InvalidThemeError

pytestmark = pytest.mark.usefixtures("clean_db")


@pytest.fixture
def auth(app_engine: AsyncEngine) -> AuthService:
    return AuthService(async_sessionmaker(app_engine, expire_on_commit=False))


async def test_login_with_seed_admin(auth: AuthService) -> None:
    token, user = await auth.login("admin", "admin")
    assert user.username == "admin"
    assert (await auth.user_for_token(token)).id == user.id


@pytest.mark.parametrize(("username", "password"), [("admin", "errada"), ("ninguem", "admin")])
async def test_login_rejects_bad_credentials(
    auth: AuthService, username: str, password: str
) -> None:
    with pytest.raises(UnauthorizedError):
        await auth.login(username, password)


async def test_missing_or_unknown_token_is_unauthorized(auth: AuthService) -> None:
    for token in (None, "", "inventado"):
        with pytest.raises(UnauthorizedError):
            await auth.user_for_token(token)


async def test_logout_revokes_session_without_deleting(
    auth: AuthService, owner_engine: AsyncEngine
) -> None:
    token, _ = await auth.login("admin", "admin")
    await auth.logout(token)
    with pytest.raises(UnauthorizedError):
        await auth.user_for_token(token)
    async with owner_engine.connect() as conn:
        row = (await conn.execute(text("SELECT revoked_at FROM auth_sessions"))).one()
    assert row.revoked_at is not None


async def test_expired_session_is_rejected(auth: AuthService, owner_engine: AsyncEngine) -> None:
    token, _ = await auth.login("admin", "admin")
    async with owner_engine.begin() as conn:
        await conn.execute(
            text("UPDATE auth_sessions SET expires_at = now() - interval '1 second'")
        )
    with pytest.raises(UnauthorizedError):
        await auth.user_for_token(token)


async def test_token_is_stored_only_as_digest(auth: AuthService, owner_engine: AsyncEngine) -> None:
    token, _ = await auth.login("admin", "admin")
    async with owner_engine.connect() as conn:
        stored = (await conn.execute(text("SELECT token_sha256 FROM auth_sessions"))).scalar_one()
    assert stored != token and len(stored) == 64


async def test_theme_is_saved_per_user(auth: AuthService) -> None:
    _, user = await auth.login("admin", "admin")
    updated = await auth.set_theme(user, "light")
    assert updated.theme == "light"
    _, again = await auth.login("admin", "admin")
    assert again.theme == "light"


async def test_invalid_theme_is_rejected(auth: AuthService) -> None:
    _, user = await auth.login("admin", "admin")
    with pytest.raises(InvalidThemeError):
        await auth.set_theme(user, "roxo")
