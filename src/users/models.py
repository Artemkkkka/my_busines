import enum

from fastapi_users_db_sqlalchemy  import SQLAlchemyBaseUserTable
from sqlalchemy import Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base
from src.mixins.timestamp_mixin import TimestampMixin


class TeamRole(str, enum.Enum):
    admin = "admin"
    manager = "manager"
    employee = "employee"


class User(Base, TimestampMixin, SQLAlchemyBaseUserTable[int]):
    role_in_team: Mapped[TeamRole] = mapped_column(
        Enum(TeamRole),
        nullable=False,
        default=TeamRole.employee,
        comment="Роль пользователя в команде"
    )

    team: Mapped["Team"] = relationship(
        back_populates="members",
        foreign_keys="User.team_id",
        doc="Команда, в которую входит пользователь"
    )

    team_id: Mapped[int] = mapped_column(
        ForeignKey("team.id", ondelete="SET NULL"),
        nullable=True,
        comment="Идентификатор команды пользователя (FK на team.id)"
    )

    authored_tasks: Mapped[list["Task"]] = relationship(
        back_populates="author",
        foreign_keys="Task.author_id",
        doc="Задачи, созданные пользователем (он — автор)"
    )

    assigned_tasks: Mapped[list["Task"]] = relationship(
        back_populates="assignee",
        foreign_keys="Task.assignee_id",
        doc="Задачи, назначенные пользователю (он — исполнитель)"
    )

    task_comments: Mapped[list["TaskComment"]] = relationship(
        back_populates="author",
        doc="Комментарии к задачам, оставленные пользователем"
    )
