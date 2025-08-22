from contextlib import asynccontextmanager

from fastapi import FastAPI
import uvicorn

from .config import settings
from .database import db_helper
from .models import Base
from src.teams.router import teams_router
from src.users.router import users_router


app = FastAPI()

app.include_router(teams_router)
app.include_router(users_router)


if __name__ == "__main__":
    uvicorn.run(
        app="main:app",
        host=settings.run.host,
        port=settings.run.port,
        reload=True
    )
