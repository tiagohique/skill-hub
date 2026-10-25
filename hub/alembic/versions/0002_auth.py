"""Usuários, sessões de login e o usuário inicial da POC.

Revision ID: 0002
"""

import os
import uuid
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op
from hub.security import hash_password

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_now = sa.text("now()")


def upgrade() -> None:
    users = op.create_table(
        "users",
        sa.Column("id", sa.Uuid, primary_key=True),
        sa.Column("username", sa.Text, nullable=False, unique=True),
        sa.Column("password_hash", sa.Text, nullable=False),
        sa.Column("theme", sa.Text, nullable=False, server_default="dark"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=_now),
        sa.CheckConstraint("theme IN ('light','dark')", name="ck_users_theme"),
    )
    op.create_table(
        "auth_sessions",
        sa.Column("token_sha256", sa.Text, primary_key=True),
        sa.Column("user_id", sa.Uuid, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=_now),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
    )
    # Usuário inicial da POC (admin/admin). Troque antes de qualquer uso fora do ambiente local.
    op.bulk_insert(
        users,
        [{"id": uuid.uuid4(), "username": "admin", "password_hash": hash_password("admin")}],
    )

    app = os.environ.get("APP_DB_USER", "hub_app")
    quoted = sa.sql.compiler.IdentifierPreparer(sa.dialects.postgresql.dialect()).quote(app)
    op.execute(f"GRANT SELECT, INSERT ON users, auth_sessions TO {quoted}")
    op.execute(f"GRANT UPDATE (theme) ON users TO {quoted}")
    op.execute(f"GRANT UPDATE (revoked_at) ON auth_sessions TO {quoted}")


def downgrade() -> None:
    op.drop_table("auth_sessions")
    op.drop_table("users")
