from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import uvicorn

from src.models.admin import UserAdmin
from src.models.admin import EvaluationAdmin
from src.models.admin import MeetingAdmin
from src.models.admin import TaskAdmin
from src.models.admin import TaskCommentAdmin
from src.models.admin import TeamAdmin

from .config import settings
from .const import API_VERSION
from src.auth.backend import auth_backend
from src.auth.users import fastapi_users
from src.auth.schemas import UserRead, UserUpdate, UserCreate
from src.evaluations.router import evaluation_router
from src.tasks.router import tasks_router
from src.teams.router import teams_router
from src.users.router import users_router
from src.meetings.router import meetings_router
from src.users.actions.route_superuser import superuser_router

from sqladmin import Admin
from src.database import db_helper


app = FastAPI()

templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )


@app.get("/calendar", response_class=HTMLResponse)
def calendar(request: Request):
    return templates.TemplateResponse(
        "calendar.html",
        {"request": request}
    )


app.include_router(
    teams_router,
    # prefix=API_VERSION,
)
app.include_router(
    tasks_router,
    # prefix=API_VERSION,
)
app.include_router(
    evaluation_router,
    # prefix=API_VERSION,
)
app.include_router(
    meetings_router,
    # prefix=API_VERSION,
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
    prefix="/my-users",
    tags=["users"],
)
app.include_router(
    superuser_router,
    # prefix=API_VERSION,
)

admin = Admin(app, db_helper.engine)

admin.add_view(UserAdmin)
admin.add_view(EvaluationAdmin)
admin.add_view(TaskAdmin)
admin.add_view(TaskCommentAdmin)
admin.add_view(MeetingAdmin)
admin.add_view(TeamAdmin)


if __name__ == "__main__":
    uvicorn.run(
        app="main:app",
        host=settings.run.host,
        port=settings.run.port,
        reload=True
    )
