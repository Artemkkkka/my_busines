from fastapi import FastAPI
import uvicorn

from .config import settings
from src.auth.backend import auth_backend
from src.auth.users import fastapi_users
from src.auth.schemas import UserRead, UserUpdate, UserCreate
from src.evaluations.router import evaluation_router
from src.tasks.router import tasks_router
from src.teams.router import teams_router
from src.users.router import users_router
from src.users.actions.route_superuser import superuser_router


app = FastAPI()


app.include_router(
    teams_router,
)
app.include_router(
    tasks_router,
)
app.include_router(
    evaluation_router,
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
