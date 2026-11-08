"""SQLAlchemy 2.0 Database Models for AegisSentinel."""

import datetime
import uuid
from typing import List, Optional

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utc_now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


class Base(DeclarativeBase):
    pass


class MissionModel(Base):
    __tablename__ = "missions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_slug: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(64), default="INITIALIZED", nullable=False)
    tokens_used: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    completed_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    exploits: Mapped[List["ExploitPayloadModel"]] = relationship(back_populates="mission", cascade="all, delete-orphan")
    patches: Mapped[List["CodePatchModel"]] = relationship(back_populates="mission", cascade="all, delete-orphan")
    receipt: Mapped[Optional["ImmunityReceiptModel"]] = relationship(back_populates="mission", uselist=False)
    audit_events: Mapped[List["AuditEventModel"]] = relationship(back_populates="mission", cascade="all, delete-orphan")


class ExploitPayloadModel(Base):
    __tablename__ = "exploit_payloads"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    mission_id: Mapped[str] = mapped_column(String(36), ForeignKey("missions.id", ondelete="CASCADE"), nullable=False)
    round_number: Mapped[int] = mapped_column(Integer, nullable=False)
    attack_vector: Mapped[str] = mapped_column(String(64), nullable=False)
    code_payload: Mapped[str] = mapped_column(Text, nullable=False)
    exit_code: Mapped[int] = mapped_column(Integer, default=-1)
    intercepted: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    mission: Mapped["MissionModel"] = relationship(back_populates="exploits")


class CodePatchModel(Base):
    __tablename__ = "code_patches"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    mission_id: Mapped[str] = mapped_column(String(36), ForeignKey("missions.id", ondelete="CASCADE"), nullable=False)
    round_number: Mapped[int] = mapped_column(Integer, nullable=False)
    diff_content: Mapped[str] = mapped_column(Text, nullable=False)
    ast_safe: Mapped[bool] = mapped_column(Boolean, default=True)
    all_passed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    mission: Mapped["MissionModel"] = relationship(back_populates="patches")


class ImmunityReceiptModel(Base):
    __tablename__ = "immunity_receipts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    mission_id: Mapped[str] = mapped_column(String(36), ForeignKey("missions.id", ondelete="CASCADE"), nullable=False)
    digest_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    ed25519_signature: Mapped[str] = mapped_column(String(128), nullable=False)
    public_key: Mapped[str] = mapped_column(String(64), nullable=False)
    runtime_engine: Mapped[str] = mapped_column(String(32), nullable=False)
    duration_ms: Mapped[float] = mapped_column(Float, nullable=False)
    memory_peak_mb: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    mission: Mapped["MissionModel"] = relationship(back_populates="receipt")


class AuditEventModel(Base):
    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    mission_id: Mapped[str] = mapped_column(String(36), ForeignKey("missions.id", ondelete="CASCADE"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    event_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    prev_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    mission: Mapped["MissionModel"] = relationship(back_populates="audit_events")
