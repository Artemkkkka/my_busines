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
from src.models.base import Base


class Status(str, enum.Enum):
    open = "open"
    in_progress = "in_progress"
    done = "done"


class Task(Base, TimestampMixin):
    name: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="Название задачи"
    )
    description: Mapped[str] = mapped_column(
        Text, comment="Подробное описание задачи в свободной форме"
    )
    deadline_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), comment="Дедлайн задачи (с таймзоной)"
    )
    status: Mapped[Status] = mapped_column(
        Enum(Status), nullable=False, default=Status.open,
        comment="Текущий статус задачи"
    )

    comments: Mapped[list["TaskComment"]] = relationship(
        back_populates="task",
        cascade="all, delete-orphan",
        order_by="TaskComment.created_at.asc()",
        doc="Комментарии к задаче, упорядочены по времени создания",
    )

    author_id: Mapped[int] = mapped_column(
        ForeignKey("user.id", ondelete="SET NULL"), nullable=True,
        comment="ID пользователя — автора задачи"
    )
    assignee_id: Mapped[int] = mapped_column(
        ForeignKey("user.id", ondelete="SET NULL"), nullable=True,
        comment="ID пользователя — исполнителя задачи (может отсутствовать)"
    )

    author: Mapped["User"] = relationship(
        foreign_keys=[author_id],
        back_populates="authored_tasks",
        lazy="joined",
        doc="Пользователь — автор задачи",
    )
    assignee: Mapped["User"] = relationship(
        foreign_keys=[assignee_id],
        back_populates="assigned_tasks",
        lazy="joined",
        doc="Пользователь — исполнитель задачи",
    )

    rating_obj: Mapped["Evaluation | None"] = relationship(
        back_populates="task",
        cascade="all, delete-orphan",
        doc="Оценка выполнения задачи (связь 1:1)",
    )
    team_id: Mapped[int] = mapped_column(
        ForeignKey("team.id", ondelete="CASCADE"),
        comment="ID команды-владельца задачи",
    )
    team: Mapped["Team"] = relationship(
        back_populates="tasks",
        doc="Команда, к которой относится задача",
    )


class TaskComment(Base, TimestampMixin,):
    task_id: Mapped[int] = mapped_column(
        ForeignKey("task.id", ondelete="CASCADE"), nullable=False,
        comment="ID связанной задачи"
    )
    author_id: Mapped[int] = mapped_column(
        ForeignKey("user.id", ondelete="SET NULL"), nullable=True,
        comment="ID пользователя — автора комментария"
    )

    task: Mapped["Task"] = relationship(
        back_populates="comments",
        doc="Задача, к которой принадлежит комментарий",
    )
    author: Mapped["User"] = relationship(
        back_populates="task_comments",
        doc="Автор комментария",
    )

    body: Mapped[str] = mapped_column(
        Text, nullable=False, comment="Текст комментария"
    )
