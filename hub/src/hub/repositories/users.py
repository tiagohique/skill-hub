import uuid
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from hub.domain.models import User
from hub.repositories.tables import auth_sessions, users


@dataclass(frozen=True)
class UserWithHash:
    user: User
    password_hash: str


class UserRepository:
    """Usuários e sessões de login. Não faz commit; a transação é do AuthService."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_by_username(self, username: str) -> UserWithHash | None:
        row = (
            await self._session.execute(select(users).where(users.c.username == username))
        ).first()
        if row is None:
            return None
        return UserWithHash(User(row.id, row.username, row.theme), row.password_hash)

    async def create_user(self, username: str, password_hash: str) -> User:
        user_id = uuid.uuid4()
        await self._session.execute(
            insert(users).values(id=user_id, username=username, password_hash=password_hash)
        )
        return User(user_id, username, "dark")

    async def set_theme(self, user_id: uuid.UUID, theme: str) -> None:
        await self._session.execute(update(users).where(users.c.id == user_id).values(theme=theme))

    async def create_session(
        self, token_sha256: str, user_id: uuid.UUID, expires_at: datetime
    ) -> None:
        await self._session.execute(
            insert(auth_sessions).values(
                token_sha256=token_sha256, user_id=user_id, expires_at=expires_at
            )
        )

    async def find_user_by_session(self, token_sha256: str, now: datetime) -> User | None:
        row = (
            await self._session.execute(
                select(users)
                .join(auth_sessions, auth_sessions.c.user_id == users.c.id)
                .where(
                    auth_sessions.c.token_sha256 == token_sha256,
                    auth_sessions.c.revoked_at.is_(None),
                    auth_sessions.c.expires_at > now,
                )
            )
        ).first()
        return None if row is None else User(row.id, row.username, row.theme)

    async def revoke_session(self, token_sha256: str, now: datetime) -> None:
        await self._session.execute(
            update(auth_sessions)
            .where(
                auth_sessions.c.token_sha256 == token_sha256, auth_sessions.c.revoked_at.is_(None)
            )
            .values(revoked_at=now)
        )
