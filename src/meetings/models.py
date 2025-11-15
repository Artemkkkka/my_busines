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
    team_id: Mapped[int] = mapped_column(
        ForeignKey("team.id", ondelete="CASCADE"), index=True,
        comment="ID команды — владельца встречи",
    )
    team: Mapped[Team] = relationship(
        backref=backref(
            "meetings", cascade="all, delete-orphan", lazy="selectin",
            doc="Список встреч команды",
        ),
        doc="Команда, в рамках которой проводится встреча",
    )
    title: Mapped[str] = mapped_column(
        String(255),
        comment="Заголовок встречи",
    )
    description: Mapped[str | None] = mapped_column(
        Text(),
        comment="Описание/повестка встречи (опционально)",
    )
    starts_at: Mapped[datetime] = mapped_column(
        DateTime, index=True,
        comment="Дата и время начала (с таймзоной)",
    )
    ends_at:   Mapped[datetime] = mapped_column(
        DateTime, index=True,
        comment="Дата и время окончания (с таймзоной)",
    )
    status: Mapped[MeetingStatus] = mapped_column(
        Enum(MeetingStatus), default=MeetingStatus.scheduled, nullable=False,
        comment="Текущий статус встречи",
    )
    participants: Mapped[list[User]] = relationship(
        "User",
        secondary=meeting_participants,
        lazy="selectin",
        backref=backref(
            "meetings", lazy="selectin",

            doc="Встречи, в которых участвует пользователь",
        ),
        doc="Участники встречи (многие-ко-многим)",
    )
