"""Definição das tabelas (SQLAlchemy Core). Espelha as migrações."""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

metadata = sa.MetaData()

_now = sa.text("now()")

skills = sa.Table(
    "skills",
    metadata,
    sa.Column("id", sa.Uuid, primary_key=True),
    sa.Column("name", sa.Text, nullable=False, unique=True),
    sa.Column("domain", sa.Text, nullable=False),
    sa.Column("owner", sa.Text, nullable=False),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=_now),
)

blobs = sa.Table(
    "blobs",
    metadata,
    sa.Column("sha256", sa.Text, primary_key=True),
    sa.Column("content", sa.LargeBinary, nullable=False),
    sa.Column("size", sa.BigInteger, nullable=False),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=_now),
)

skill_versions = sa.Table(
    "skill_versions",
    metadata,
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

skill_version_files = sa.Table(
    "skill_version_files",
    metadata,
    sa.Column("version_id", sa.Uuid, sa.ForeignKey("skill_versions.id"), primary_key=True),
    sa.Column("path", sa.Text, primary_key=True),
    sa.Column("sha256", sa.Text, sa.ForeignKey("blobs.sha256"), nullable=False),
    sa.Column("size", sa.BigInteger, nullable=False),
)

channels = sa.Table(
    "channels",
    metadata,
    sa.Column("skill_id", sa.Uuid, sa.ForeignKey("skills.id"), primary_key=True),
    sa.Column("channel", sa.Text, primary_key=True),
    sa.Column("version_id", sa.Uuid, sa.ForeignKey("skill_versions.id"), nullable=True),
    sa.CheckConstraint("channel IN ('beta','stable')", name="ck_channels_channel"),
)

audit_events = sa.Table(
    "audit_events",
    metadata,
    sa.Column("id", sa.Uuid, primary_key=True),
    sa.Column("actor", sa.Text, nullable=False),
    sa.Column("action", sa.Text, nullable=False),
    sa.Column("skill", sa.Text, nullable=False),
    sa.Column("version", sa.Text, nullable=True),
    sa.Column("at", sa.DateTime(timezone=True), nullable=False, server_default=_now),
)

users = sa.Table(
    "users",
    metadata,
    sa.Column("id", sa.Uuid, primary_key=True),
    sa.Column("username", sa.Text, nullable=False, unique=True),
    sa.Column("password_hash", sa.Text, nullable=False),
    sa.Column("theme", sa.Text, nullable=False, server_default="dark"),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=_now),
    sa.CheckConstraint("theme IN ('light','dark')", name="ck_users_theme"),
)

auth_sessions = sa.Table(
    "auth_sessions",
    metadata,
    sa.Column("token_sha256", sa.Text, primary_key=True),
    sa.Column("user_id", sa.Uuid, sa.ForeignKey("users.id"), nullable=False),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=_now),
    sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
)
