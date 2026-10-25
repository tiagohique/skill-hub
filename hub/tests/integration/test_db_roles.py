import pytest
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.ext.asyncio import AsyncEngine


async def test_app_role_can_connect(app_engine: AsyncEngine) -> None:
    async with app_engine.connect() as conn:
        result = await conn.execute(text("SELECT current_user"))
    assert result.scalar_one() == "hub_app"


async def test_app_role_cannot_create_table(app_engine: AsyncEngine) -> None:
    async with app_engine.begin() as conn:
        with pytest.raises(ProgrammingError, match="permission denied"):
            await conn.execute(text("CREATE TABLE x (i int)"))
