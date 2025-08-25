from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.users.models import User
from src.database import db_helper
from src.auth.users import current_user

SessionDep = Annotated[AsyncSession, Depends(db_helper.session_getter)]
CurrentUser = Annotated[User, Depends(current_user)]