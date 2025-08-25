from typing import Optional
from fastapi_users import schemas
from pydantic import EmailStr, BaseModel


class UserRead(schemas.BaseUser[int]):
    pass


class UserCreate(schemas.BaseUserCreate):
    pass


class UserUpdate(BaseModel):
    email: Optional[EmailStr]

