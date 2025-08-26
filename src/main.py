from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, Security, HTTPException, APIRouter
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
import uvicorn

from .config import settings
from .database import db_helper
from .models import Base
from src.auth.manager import get_user_manager
from src.auth.backend import auth_backend
from src.auth.users import fastapi_users
from src.auth.schemas import UserRead, UserUpdate, UserCreate
from src.core.dependencies import CurrentUser
from src.teams.router import teams_router
from src.users.crud import delete_user as delete_user_crud
from src.users.router import users_router
from src.users.actions.route_superuser import superuser_router


app = FastAPI()


http_bearer = HTTPBearer(auto_error=True)

app.include_router(
    teams_router,
    # dependencies=[Depends(http_bearer)],
)

app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="/auth",
    tags=["auth"],
)

app.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"],
)
app.include_router(
    users_router,
    prefix="/users",
    tags=["users"],

)
app.include_router(
    superuser_router,
)


if __name__ == "__main__":
    uvicorn.run(
        app="main:app",
        host=settings.run.host,
        port=settings.run.port,
        reload=True
    )
