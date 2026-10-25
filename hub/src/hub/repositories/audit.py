import uuid

from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession

from hub.repositories.tables import audit_events


class AuditRepository:
    """Trilha de auditoria: só inserção. Não faz commit."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def record(self, actor: str, action: str, skill: str, version: str | None) -> None:
        await self._session.execute(
            insert(audit_events).values(
                id=uuid.uuid4(), actor=actor, action=action, skill=skill, version=version
            )
        )
