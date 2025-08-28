from datetime import datetime
import enum

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.mixins.timestamp_mixin import TimestampMixin
from src.models import Base


class Status(str, enum.Enum):
    open = "open"
    in_progress = "in_progress"
    done = "done"


class Task(Base, TimestampMixin):
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text)
    deadline_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[Status] = mapped_column(
        Enum(Status), nullable=False, default=Status.open
    )
    comments: Mapped[list["TaskComment"]] = relationship(
        back_populates="task",
        cascade="all, delete-orphan",
        order_by="TaskComment.created_at.asc()",
    )

    author_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="RESTRICT"), nullable=False)
    assignee_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="SET NULL"))

    author: Mapped["User"] = relationship(
        "User",
        foreign_keys=[author_id],
        back_populates="authored_tasks",
        lazy="joined",
    )
    assignee: Mapped["User"] = relationship(
        "User",
        foreign_keys=[assignee_id],
        back_populates="assigned_tasks",
        lazy="joined",
    )

    team_id: Mapped[int] = mapped_column(ForeignKey("team.id", ondelete="SET NULL"))
    team: Mapped["Team"] = relationship("Team", back_populates="tasks")
