from fastapi import APIRouter


teams_router = APIRouter(
    prefix="/teams",
    tags=["teams"],
)
