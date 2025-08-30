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
    assignee_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="SET NULL"), nullable=True)

    author: Mapped["User"] = relationship(
        foreign_keys=[author_id],
        back_populates="authored_tasks",
        lazy="joined",
    )
    assignee: Mapped["User"] = relationship(
        foreign_keys=[assignee_id],
        back_populates="assigned_tasks",
        lazy="joined",
    )
    rating_obj: Mapped["Evaluation | None"] = relationship(
        back_populates="task",
        cascade="all, delete-orphan",
    )

    team_id: Mapped[int] = mapped_column(ForeignKey("team.id", ondelete="CASCADE"))
    team: Mapped["Team"] = relationship(back_populates="tasks")


class TaskComment(Base, TimestampMixin,):
    task_id: Mapped[int] = mapped_column(ForeignKey("task.id", ondelete="CASCADE"), nullable=False)
    author_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="RESTRICT"), nullable=False)

    task: Mapped["Task"] = relationship(back_populates="comments")
    author: Mapped["User"] = relationship(back_populates="task_comments")

    body: Mapped[str] = mapped_column(Text, nullable=False)
