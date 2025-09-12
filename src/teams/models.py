from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.mixins.timestamp_mixin import TimestampMixin
from src.models.base import Base


class Team(Base, TimestampMixin):
    name: Mapped[str]

    owner_id: Mapped[int | None] = mapped_column(ForeignKey('user.id'))
    owner: Mapped["User"] = relationship(
        foreign_keys="Team.owner_id",
    )
    members: Mapped[list["User"]] = relationship(back_populates="team", foreign_keys="User.team_id")
    tasks: Mapped[list["Task"]] = relationship(back_populates="team")
