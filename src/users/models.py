import enum

from sqlalchemy import DateTime, Enum, func
from sqlalchemy.orm import Mapped, mapped_column

from src.models import Base


class TeamRole(str, enum.Enum):
    admin = "admin"
    manager = "manager"
    employee = "employee"


class User(Base):
    email: Mapped[str]
    password: Mapped[str]
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

    is_superuser: Mapped[bool] = mapped_column(default=False)
