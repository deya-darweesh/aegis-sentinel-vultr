"""0001 Initial AegisSentinel Schema

Revision ID: 0001_initial_schema
Revises: None
Create Date: 2026-11-08 12:00:00.000000
"""

from typing import Optional, Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial_schema"
down_revision: Optional[str] = None
branch_labels: Optional[Sequence[str]] = None
depends_on: Optional[Sequence[str]] = None


def upgrade() -> None:
    # 1. Missions Table
    op.create_table(
        "missions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("task_slug", sa.String(128), nullable=False, index=True),
        sa.Column("status", sa.String(64), nullable=False, server_default="INITIALIZED"),
        sa.Column("tokens_used", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )

    # 2. Exploit Payloads Table
    op.create_table(
        "exploit_payloads",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("mission_id", sa.String(36), sa.ForeignKey("missions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("round_number", sa.Integer(), nullable=False),
        sa.Column("attack_vector", sa.String(64), nullable=False),
        sa.Column("code_payload", sa.Text(), nullable=False),
        sa.Column("exit_code", sa.Integer(), nullable=False, server_default="-1"),
        sa.Column("intercepted", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_exploit_payloads_mission_id", "exploit_payloads", ["mission_id"])

    # 3. Code Patches Table
    op.create_table(
        "code_patches",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("mission_id", sa.String(36), sa.ForeignKey("missions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("round_number", sa.Integer(), nullable=False),
        sa.Column("diff_content", sa.Text(), nullable=False),
        sa.Column("ast_safe", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("all_passed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_code_patches_mission_id", "code_patches", ["mission_id"])

    # 4. Immunity Receipts Table
    op.create_table(
        "immunity_receipts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("mission_id", sa.String(36), sa.ForeignKey("missions.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("digest_sha256", sa.String(64), nullable=False),
        sa.Column("ed25519_signature", sa.String(128), nullable=False),
        sa.Column("public_key", sa.String(64), nullable=False),
        sa.Column("runtime_engine", sa.String(32), nullable=False),
        sa.Column("duration_ms", sa.Float(), nullable=False),
        sa.Column("memory_peak_mb", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    # 5. Audit Events Table
    op.create_table(
        "audit_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("mission_id", sa.String(36), sa.ForeignKey("missions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("event_hash", sa.String(64), nullable=False),
        sa.Column("prev_hash", sa.String(64), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_audit_events_mission_id", "audit_events", ["mission_id"])


def downgrade() -> None:
    op.drop_table("audit_events")
    op.drop_table("immunity_receipts")
    op.drop_table("code_patches")
    op.drop_table("exploit_payloads")
    op.drop_table("missions")
