from datetime import datetime
from typing import Optional

from fastapi import HTTPException


async def _validate_times(starts_at: Optional[datetime], ends_at: Optional[datetime]) -> None:
    if starts_at is not None and ends_at is not None:
        if ends_at <= starts_at:
            raise HTTPException(status_code=400, detail="ends_at must be after starts_at")
