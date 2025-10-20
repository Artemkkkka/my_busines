# models/meeting.py
from __future__ import annotations
from datetime import datetime
from enum import StrEnum

from sqlalchemy import (
    ForeignKey, String, Text, Integer, DateTime, Enum, Index,
    Table, Column,
    func,
)
from sqlalchemy.dialects.postgresql import ExcludeConstraint
from sqlalchemy.orm import (
    Mapped, mapped_column, relationship, backref
)


from src.models.base import Base
from src.mixins.timestamp_mixin import TimestampMixin
from src.teams.models import Team
from src.users.models import User


meeting_participants = Table(
    "meeting_participants",
    Base.metadata,
    Column("meeting_id", ForeignKey("meeting.id", ondelete="CASCADE"), primary_key=True),
    Column("user_id", ForeignKey("user.id", ondelete="CASCADE"), primary_key=True),
    Index("ix_mp_user", "user_id"),
)


class MeetingStatus(StrEnum):
    scheduled = "scheduled"
    canceled  = "canceled"


class Meeting(Base, TimestampMixin):

    team_id: Mapped[int] = mapped_column(ForeignKey("team.id", ondelete="CASCADE"), index=True)
    team: Mapped[Team] = relationship(
        backref=backref("meetings", cascade="all, delete-orphan", lazy="selectin")
    )

    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text())

    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    ends_at:   Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)

    status: Mapped[MeetingStatus] = mapped_column(
        Enum(MeetingStatus), default=MeetingStatus.scheduled, nullable=False
    )

    participants: Mapped[list[User]] = relationship(
        "User",
        secondary=meeting_participants,
        lazy="selectin",
        backref=backref("meetings", lazy="selectin"),
    )
