from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    telegram_id: int
    name: str
    email: Optional[EmailStr] = None
    profile_picture: Optional[str] = None
    balance: float = 0.0
    level: int = 1
    ranking: int = 0

class UserCreate(UserBase):
    pass

class UserResponse(UserBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True
