from __future__ import annotations
from datetime import datetime

from sqlalchemy import SmallInteger, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base


class Evaluation(Base):
    task_id: Mapped[int] = mapped_column(
        ForeignKey("task.id", ondelete="CASCADE"), nullable=False,
        comment="ID задачи, к которой относится оценка"
    )
    value: Mapped[int] = mapped_column(
        SmallInteger, nullable=False,
        comment="Числовая оценка выполнения (например, 1–5)",
    )
    rated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        comment="Время, когда была выставлена оценка (с таймзоной)",
    )

    task: Mapped["Task"] = relationship(
        back_populates="rating_obj",
        doc="Связанная задача",
    )
