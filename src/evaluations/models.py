from __future__ import annotations
from datetime import datetime

from sqlalchemy import SmallInteger, ForeignKey, DateTime, CheckConstraint, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base


class Evaluation(Base):
    task_id: Mapped[int] = mapped_column(ForeignKey("task.id", ondelete="CASCADE"), nullable=False)
    value: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    rated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    task: Mapped["Task"] = relationship(back_populates="rating_obj")
