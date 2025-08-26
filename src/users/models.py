import enum

from fastapi_users_db_sqlalchemy  import SQLAlchemyBaseUserTable
from sqlalchemy import DateTime, Enum, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models import Base


class TeamRole(str, enum.Enum):
    admin = "admin"
    manager = "manager"
    employee = "employee"


class User(Base, SQLAlchemyBaseUserTable[int]):
    role_in_team: Mapped[TeamRole] = mapped_column(
        Enum(TeamRole),
        nullable=False,
        default=TeamRole.employee
    )
    created_at: Mapped["DateTime"] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped["DateTime"] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    team: Mapped["Team"] = relationship(back_populates="members", foreign_keys="User.team_id")
    team_id: Mapped[int] = mapped_column(ForeignKey("team.id"), nullable=True)
