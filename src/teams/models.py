from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.mixins.timestamp_mixin import TimestampMixin
from src.models.base import Base


class Team(Base, TimestampMixin):
    name: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="Название команды"
    )
    owner_id: Mapped[int | None] = mapped_column(
        ForeignKey('user.id',  ondelete="SET NULL"),
        comment="ID владельца команды (опционально)",
    )
    owner: Mapped["User"] = relationship(
        foreign_keys="Team.owner_id",
        doc="Пользователь — владелец команды",
    )
    members: Mapped[list["User"]] = relationship(
        back_populates="team",
        foreign_keys="User.team_id",
        doc="Участники команды",
    )
    tasks: Mapped[list["Task"]] = relationship(
        back_populates="team",
        doc="Задачи, принадлежащие команде",
    )
