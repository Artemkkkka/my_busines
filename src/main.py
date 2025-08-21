from fastapi import FastAPI
import uvicorn

from .config import settings
from src.teams.router import teams_router

app = FastAPI()
app.include_router(teams_router)


if __name__ == "__main__":
    uvicorn.run(
        app="main:app",
        host=settings.run.host,
        port=settings.run.port,
        reload=True
    )
