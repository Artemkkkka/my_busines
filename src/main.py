from contextlib import asynccontextmanager

from fastapi import FastAPI
import uvicorn

from config import settings
from database import db_helper
from teams.router import teams_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await db_helper.dispose()

app = FastAPI(
    lifespan=lifespan,
)
app.include_router(teams_router)


if __name__ == "__main__":
    uvicorn.run(
        app="main:app",
        host=settings.run.host,
        port=settings.run.port,
        reload=True
    )
