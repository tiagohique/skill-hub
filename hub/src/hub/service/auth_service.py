from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from hub.domain.errors import HubError, UnauthorizedError
from hub.domain.models import User
from hub.repositories.users import UserRepository
from hub.security import hash_password, new_token, token_digest, verify_password

SESSION_DAYS = 7
THEMES = ("light", "dark")
# Hash de uma senha qualquer: gasta o mesmo tempo quando o usuário não existe.
_DUMMY_HASH = hash_password("dummy")


class InvalidThemeError(HubError):
    code = "invalid_request"


class AuthService:
    """Login, sessões e preferência de tema. Cada operação abre a própria transação."""

    def __init__(self, sessions: async_sessionmaker[AsyncSession]) -> None:
        self._sessions = sessions

    async def login(self, username: str, password: str) -> tuple[str, User]:
        async with self._sessions.begin() as session:
            repo = UserRepository(session)
            found = await repo.find_by_username(username)
            ok = verify_password(password, found.password_hash if found else _DUMMY_HASH)
            if found is None or not ok:
                raise UnauthorizedError("Usuário ou senha inválidos.")
            token = new_token()
            expires = datetime.now(UTC) + timedelta(days=SESSION_DAYS)
            await repo.create_session(token_digest(token), found.user.id, expires)
            return token, found.user

    async def user_for_token(self, token: str | None) -> User:
        if not token:
            raise UnauthorizedError("Faça login para continuar.")
        async with self._sessions() as session:
            user = await UserRepository(session).find_user_by_session(
                token_digest(token), datetime.now(UTC)
            )
        if user is None:
            raise UnauthorizedError("Sessão expirada. Faça login novamente.")
        return user

    async def logout(self, token: str | None) -> None:
        if not token:
            return
        async with self._sessions.begin() as session:
            await UserRepository(session).revoke_session(token_digest(token), datetime.now(UTC))

    async def set_theme(self, user: User, theme: str) -> User:
        if theme not in THEMES:
            raise InvalidThemeError("O tema deve ser 'light' ou 'dark'.")
        async with self._sessions.begin() as session:
            await UserRepository(session).set_theme(user.id, theme)
        return User(user.id, user.username, theme)
