"""Esquema inicial e permissões mínimas do usuário da aplicação.

Revision ID: 0001
"""

import os
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_now = sa.text("now()")


def upgrade() -> None:
    op.create_table(
        "skills",
        sa.Column("id", sa.Uuid, primary_key=True),
        sa.Column("name", sa.Text, nullable=False, unique=True),
        sa.Column("domain", sa.Text, nullable=False),
        sa.Column("owner", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=_now),
    )
    op.create_table(
        "blobs",
        sa.Column("sha256", sa.Text, primary_key=True),
        sa.Column("content", sa.LargeBinary, nullable=False),
        sa.Column("size", sa.BigInteger, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=_now),
    )
    op.create_table(
        "skill_versions",
        sa.Column("id", sa.Uuid, primary_key=True),
        sa.Column("skill_id", sa.Uuid, sa.ForeignKey("skills.id"), nullable=False),
        sa.Column("version", sa.Text, nullable=False),
        sa.Column("status", sa.Text, nullable=False),
        sa.Column("frontmatter", JSONB, nullable=False),
        sa.Column("bundle_sha256", sa.Text, nullable=False),
        sa.Column("created_by", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=_now),
        sa.UniqueConstraint("skill_id", "version", name="uq_skill_versions_skill_id_version"),
        sa.CheckConstraint(
            "status IN ('draft','beta','stable','deprecated','retired')",
            name="ck_skill_versions_status",
        ),
    )
    op.create_table(
        "skill_version_files",
        sa.Column("version_id", sa.Uuid, sa.ForeignKey("skill_versions.id"), primary_key=True),
        sa.Column("path", sa.Text, primary_key=True),
        sa.Column("sha256", sa.Text, sa.ForeignKey("blobs.sha256"), nullable=False),
        sa.Column("size", sa.BigInteger, nullable=False),
    )
    op.create_table(
        "channels",
        sa.Column("skill_id", sa.Uuid, sa.ForeignKey("skills.id"), primary_key=True),
        sa.Column("channel", sa.Text, primary_key=True),
        sa.Column("version_id", sa.Uuid, sa.ForeignKey("skill_versions.id"), nullable=True),
        sa.CheckConstraint("channel IN ('beta','stable')", name="ck_channels_channel"),
    )
    op.create_table(
        "audit_events",
        sa.Column("id", sa.Uuid, primary_key=True),
        sa.Column("actor", sa.Text, nullable=False),
        sa.Column("action", sa.Text, nullable=False),
        sa.Column("skill", sa.Text, nullable=False),
        sa.Column("version", sa.Text, nullable=True),
        sa.Column("at", sa.DateTime(timezone=True), nullable=False, server_default=_now),
    )

    # Imutabilidade imposta pelo banco: o usuário da aplicação só insere e lê.
    # Exceções: skill_versions.status e channels.version_id (promoção e depreciação).
    # Nenhum DELETE nem TRUNCATE em lugar nenhum.
    app = os.environ.get("APP_DB_USER", "hub_app")
    quoted = sa.sql.compiler.IdentifierPreparer(sa.dialects.postgresql.dialect()).quote(app)
    op.execute(f"GRANT USAGE ON SCHEMA public TO {quoted}")
    op.execute(
        f"GRANT SELECT, INSERT ON blobs, skill_version_files, audit_events, skills, "
        f"skill_versions, channels TO {quoted}"
    )
    op.execute(f"GRANT UPDATE (status) ON skill_versions TO {quoted}")
    op.execute(f"GRANT UPDATE (version_id) ON channels TO {quoted}")


def downgrade() -> None:
    for table in (
        "audit_events",
        "channels",
        "skill_version_files",
        "skill_versions",
        "blobs",
        "skills",
    ):
        op.drop_table(table)
